import re
import pathlib

from pyglottolog import Glottolog
from pyglottolog.fts import search
from pybtex.database import parse_string

from cldfbench import Dataset as BaseDataset, CLDFSpec

HEADER = [
    'language', 'iso', 'genus', 'family', 'lat', 'lon', 'val',
    't3',
    't4',
    't5',
    't6',
    't7',
    't8',
    't9',
    't10',
    't13',
]
# Baule,tul,Kwa,Niger-Congo,7dN,5dW,N-A-Num-Dem,,,,,,,,,


def iter_entries(lines):
    agg = []
    for line in lines:
        line = line.strip()
        if line:
            if re.match('[A-Z] [A-Z]', line):
                if agg:
                    yield ' '.join(agg)
                agg = [line]
            else:
                agg.append(line)
    if agg:
        yield ' '.join(agg)


def parse_authors(s):
    if s.endswith(' .'):
        s = s[:-2].strip()
    return [
        re.sub('(^| )(?P<initial>[A-Z]) (?P<rem>[A-Z]+)', lambda m: ' {0}{1}'.format(m.group('initial'), m.group('rem').lower()), ss).strip()
        for ss in s.split(' AND ')]


def parse_entry(e):
    yearp = re.compile('\s+(?P<refyear>(?P<year>[0-9]{4})[abcde]?)(\s+\[[0-9\-]+\])?\.\s*')
    year = yearp.search(e)
    assert year
    author = e[:year.start()].strip()
    title = e[year.end():].split('.')[0].strip()
    authors = parse_authors(author)
    return (
        authors,
        year.group('year'),
        title,
        '{0} {1}'.format(' and '.join([a.split(',')[0].strip() for a in authors]), year.group('refyear')))


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "dryerorder"

    def cldf_specs(self):
        return CLDFSpec(module='StructureDataset', dir=self.cldf_dir)

    def cmd_download(self, args):
        # https://muse.jhu.edu/article/712564/file/supp02.csv
        # https://muse.jhu.edu/article/712564/file/supp01.pdf

        bd = parse_string(self.raw_dir.read('sources.bib'), 'bibtex')
        keys = {e.fields['key']: k for k, e in bd.entries.items()}

        langs = {r[0]: dict(zip(HEADER, r)) for r in self.raw_dir.read_csv('Dryer_DNAnTable.txt', encoding='macroman')}
        langs_with_val = {r for r in langs if langs[r]['val']}


    def cmd_makecldf(self, args):
        args.writer.cldf.add_component('ParameterTable')
        args.writer.cldf.add_component('LanguageTable')
        args.writer.cldf.add_component('CodeTable')

        #Language_Name,ISO_code,Genus,Family,Latitude,Longitude,Order_of_Dem_Num_A_N,Table_3,Table_4,Table_5,Table_6,Table_7,Table_8,Table_9,Table_10,Table_13_and_13B
