#-*- coding: utf-8 -*-

import os

from elftools.elf.elffile import ELFFile

class DwarfExtractor(object):

    def __init__(self):
        self.types_cache = dict()

    def extract(self, binary, logfile):
        protos = dict()
        with open(binary, 'rb') as f:
            elf_file = ELFFile(f)

            if not elf_file.has_dwarf_info():
                print('    File has no debug info (DWARF format expected) !')
                return protos

            dwarf_info = elf_file.get_dwarf_info()
            for CU in dwarf_info.iter_CUs():
                for DIE in CU.iter_DIEs():
                    self.__extract_DIE(CU, DIE, protos)

        with open(logfile, "w") as f:
            for name, (entry, ret) in protos.items():
                f.write("{}:{}:{}\n".format(name, entry, ret))

    def __extract_DIE(self, CU, DIE, protos):
        if DIE.tag == 'DW_TAG_subprogram':
            if ('DW_AT_name' not in DIE.attributes
                    or 'DW_AT_declaration' in DIE.attributes):
                return

            name = self.DIE_name(DIE)
            if name in protos:
                return

            protos[name] = self.DIE_loc(DIE)

    def DIE_loc(self, DIE):
        if 'DW_AT_low_pc' in DIE.attributes:
            entry = DIE.attributes['DW_AT_low_pc'].value
            ret = entry + DIE.attributes['DW_AT_high_pc'].value
            return  (entry, ret)
        else:
            return (0,0)

    def DIE_name(self, DIE):
        if 'DW_AT_name' in DIE.attributes:
            return DIE.attributes['DW_AT_name'].value
        else:
            return "<???>"

