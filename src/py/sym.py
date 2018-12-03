#-*- coding: utf-8 -*-

from elftools.elf.elffile import ELFFile
import os

from src.py.log import Log

class SymExtractor(object):

    def extract(self, binary, logfile):
        protos = dict()
        with open(binary, 'rb') as f:
            e = ELFFile(f)
            symtable = e.get_section_by_name(".symtab")
            if not symtable:
                Log.stderr("symbole table not found")
                return protos
            for entry in symtable.iter_symbols():
                if "FUNC" in entry['st_info'].type:
                    name = entry.name
                    addr = entry["st_value"]
                    ret = entry["st_value"]
                    protos[addr] = (name, addr, ret)
            dynsym = e.get_section_by_name(".dynsym")
            reloc = e.get_section_by_name(".rela.plt")
            plt_base = e.get_section_by_name(".plt")['sh_addr']
            # Additionally add plt entries
            for idx, entry in enumerate(reloc.iter_relocations()):
                name = dynsym.get_symbol(entry['r_info_sym']).name + "@plt"
                addr = plt_base + 16*(idx + 1)
                protos[addr] = (name, addr, addr)

        with open(logfile, "w") as f:
            for (name, entry, ret) in protos.values():
                f.write("{}:{}:{}\n".format(name, entry, ret))

