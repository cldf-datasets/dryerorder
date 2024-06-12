import pathlib
import collections

from clldutils.coordinates import Coordinates
from clldutils.misc import slug
from clldutils.text import split_text_with_context
from pybtex.database import parse_string

from cldfbench import Dataset as BaseDataset, CLDFSpec

HEADER = [
    'language', 'iso', 'genus', 'family', 'lat', 'lon',
    'Table1',
    'Table3',
    'Table4',
    'Table5',
    'Table6',
    'Table7',
    'Table8',
    'Table9',
    'Table10',
    'Table13',
]
# Baule,tul,Kwa,Niger-Congo,7dN,5dW,N-A-Num-Dem,,,,,,,,,


def clean_coords(c):
    c = c.replace('?', '')
    return {'21d43dN': '21d43N'}.get(c, c)


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "dryerorder"

    def cldf_specs(self):
        return CLDFSpec(module='StructureDataset', dir=self.cldf_dir)

    def cmd_download(self, args):
        # https://muse.jhu.edu/article/712564/file/supp02.csv
        # https://muse.jhu.edu/article/712564/file/supp01.pdf
        pass

    def cmd_makecldf(self, args):
        args.writer.cldf.add_component('ParameterTable')
        args.writer.cldf.add_component('LanguageTable', 'Genus', 'Family')
        args.writer.cldf.add_component('CodeTable', 'Map_Icon')
        args.writer.cldf.add_sources(parse_string(self.raw_dir.read('sources.bib'), 'bibtex'))

        etc_parameters = {
            parameter['ID']: parameter
            for parameter in self.etc_dir.read_csv(
                'parameters.csv', dicts=True)}
        for row in self.raw_dir.read_csv('parameters.csv', dicts=True):
            parameter_id = row['ID']
            etc_parameter = etc_parameters.get(parameter_id) or {}
            args.writer.objects['ParameterTable'].append(dict(
                ID=row['ID'],
                Name=etc_parameter.get('Name') or row['ID'],
                Description=etc_parameter.get('Description') or row['Description'],
            ))

        codes = collections.defaultdict(dict)
        for row in self.raw_dir.read_csv('codes.csv', dicts=True):
            args.writer.objects['CodeTable'].append(dict(
                ID=row['ID'],
                Name=row['Name'],
                Description=row['Description'],
                Parameter_ID=row['Parameter_ID'],
                Map_Icon=row['Map_Icon'],
                # FIXME: add abbr!
            ))
            codes[row['Parameter_ID']][row['Name']] = row['ID']

        glottocodes = {r['name']: r['glottocode'] for r in self.etc_dir.read_csv('languages.csv', dicts=True)}
        sources = {r['language']: r for r in self.raw_dir.read_csv('sources.csv', dicts=True)}
        vid = 0
        gl_by_iso = {}
        gl_by_id = {}
        for l in args.glottolog.api.languoids():
            if l.iso:
                gl_by_iso[l.iso] = l
            gl_by_id[l.id] = l

        for row in self.raw_dir.read_csv('Dryer_DNAnTable.txt', encoding='macroman'):
            row = dict(zip(HEADER, row))
            coords = Coordinates(clean_coords(row['lat']), clean_coords(row['lon']))
            iso = row['iso'] if row['iso'] != '--' else None
            lid = slug(row['language'] + (row['iso'] or ''))
            if row['language'] in glottocodes:
                glang = gl_by_id[glottocodes[row['language']]]
            else:
                glang = gl_by_iso.get(row['iso'])
            if not glang:
                print(row['language'], row['iso'])
            args.writer.objects['LanguageTable'].append(dict(
                ID=lid,
                Name=row['language'],
                Latitude=coords.latitude,
                Longitude=coords.longitude,
                ISO639P3code=iso,
                Glottocode=glang.id if glang else None,
                Genus=row['genus'],
                Family=row['family'],
            ))
            for p in args.writer.objects['ParameterTable']:
                source, comment = [], None
                if p['ID'] == 'Table1' and row['language'] in sources:
                    source = split_text_with_context(
                        sources[row['language']]['sources'], separators=';', brackets={'[': ']'})
                    comment = sources[row['language']]['comment']
                if row[p['ID']]:
                    vid += 1
                    args.writer.objects['ValueTable'].append(dict(
                        ID=str(vid),
                        Language_ID=lid,
                        Parameter_ID=p['ID'],
                        Value=row[p['ID']],
                        Code_ID=codes[p['ID']][row[p['ID']]],
                        Source=source,
                        Comment=comment,
                    ))

            #langs_with_val = {r for r in langs if langs[r]['Table1']}
