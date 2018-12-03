#ifndef __INS_H__
#define __INS_H__

#include <iostream>
#include <fstream>

#include "pin.H"

typedef struct ins {
    string *str;
    ADDRINT addr;
    string *img_name;
    ADDRINT offset;
    UINT64 nb_hit;
    struct ins *next;
} ins_t;

/* Add an instruction to the linked list of instructions
   given in parameter. Return the new pointer to the head
   of the list */
ins_t *add_ins(ins_t *list_of_ins, string *str, ADDRINT addr) {
    if (str == NULL)
        return list_of_ins;
    /* Check if addr already in list */
    ins_t *senti = list_of_ins;
    while (senti) {
        if (senti->addr == addr) {
            senti->nb_hit += 1;
            return list_of_ins;
        }
        senti = senti->next;
    }
    ins_t *ins = (ins_t *) malloc(sizeof(ins_t));
    ins->str = str;
    ins->addr = addr;
    PIN_LockClient();
    IMG img = IMG_FindByAddress(addr);
    PIN_UnlockClient();
    if (IMG_Valid(img)) {
        ins->img_name = new string(IMG_Name(img));
        ins->offset = addr - IMG_LoadOffset(img);
    } else {
        ins->img_name = new string("");
        ins->offset = addr;
    }
    ins->nb_hit = 1;
    ins->next = list_of_ins;
    return ins;
}

VOID print_list_of_ins(ofstream& ofile, ins_t *ins) {
    ins_t *senti = ins;
    while (senti) {
        ofile << "I:" << *(senti->img_name) << ":" << senti->offset << ":" << *(senti->str) << ":" << senti->nb_hit << endl;        
        senti = senti->next;
    }
    return;
}

#endif
