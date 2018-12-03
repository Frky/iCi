#ifndef __FN_BOUND_H__
#define __FN_BOUND_H__

#include <iostream>
#include <fstream>
#include "pin.H"

#include "ins.h"

#define TABLE_SIZE 262144
#define KEY(x) (x >> 2) %TABLE_SIZE

/* Structure for function boundaries from DWARF info */
typedef struct fn_bound {
    ADDRINT entry;
    ADDRINT ret;
    UINT64 calls;
    string *name;
    string *img_name;
    ADDRINT offset;
    struct fn_bound *next;
    struct fn_bound *prev;
    ins_t *ins;
} fn_bound_t;

BOOL _created = false;

fn_bound_t **fn_init_table(void) {
    fn_bound_t **table = (fn_bound_t **) malloc(TABLE_SIZE * sizeof(fn_bound_t *));
    for (int i = 0; i < TABLE_SIZE; i++) {
        table[i] = NULL;
    }
    return table;
}

fn_bound_t *fn_find(fn_bound_t **table, ADDRINT addr) {
    fn_bound_t *senti = table[KEY(addr)];
    while (senti) {
        if (senti->entry == addr) {
            /* If IMG was not found earlier
               update infos */
            if (senti->img_name == NULL) {
                PIN_LockClient();
                IMG img = IMG_FindByAddress(senti->entry);
                PIN_UnlockClient();
                if (IMG_Valid(img)) {
                    senti->img_name = new string(IMG_Name(img));
                    senti->offset = senti->entry - IMG_LoadOffset(img);
                }
            }
            return senti;
        }
        senti = senti->next;
    }
    return NULL;
}

void fn_add_retaddr(fn_bound_t **table, ADDRINT entry, ADDRINT retaddr) {
    fn_bound_t *f = fn_find(table, entry);
    if (f && f->ret < retaddr)
        f->ret = retaddr;
}

BOOL fn_created(void) {
    return _created;
}

/* Add a function to the list of known functions */
fn_bound_t *fn_add(fn_bound_t **table, string fname, ADDRINT entry, ADDRINT ret) {
    _created = true;
    /* Check if we already know this function */
    fn_bound_t *f = fn_find(table, entry);
    if (f) {
        _created = false;
        return f;
    }
    /* If not, add it to the linked list */
    f = (fn_bound_t *) malloc(sizeof(fn_bound_t));
    f->name = new string(fname);
    f->entry = entry;
    f->ret = ret;
    f->calls = 0;
    f->ins = NULL;
    PIN_LockClient();
    IMG img = IMG_FindByAddress(entry);
    PIN_UnlockClient();
    if (!IMG_Valid(img)) {
        f->img_name = NULL;
        f->offset = entry;
    } else {
        f->img_name = new string(IMG_Name(img));
        f->offset = entry - IMG_LoadOffset(img);
    }
    f->next = table[KEY(entry)];
    if (f->next)
        f->next->prev = f;
    f->prev = NULL;
    table[KEY(entry)] = f;
    return f;
}


void fn_print_one(ofstream& ofile, fn_bound_t *f) {
    if (!(f->img_name)) {
        f->img_name = new string("");
    }
    ofile << "F:"<< *(f->img_name) << ":" << f->offset << ":" << *(f->name) << ":" << f->calls << endl;
    print_list_of_ins(ofile, f->ins); 
}

BOOL fn_cross_bound(fn_bound_t **table, ADDRINT from, ADDRINT to) {
    fn_bound_t *senti;
    for (int i = 0; i < TABLE_SIZE; i++) {
        senti = table[i];
        while (senti) {
            if (from < senti->entry && senti->entry < to)
                return true;
            senti = senti->next;
        }
    }
    return false;
}

void fn_flush(fn_bound_t **table) {
    fn_bound_t *senti;
    for (int i = 0; i < TABLE_SIZE; i++) { 
        senti = table[i];
        while (senti) {
            fn_bound_t *tmp = senti;
            senti = senti->next;
            free(tmp);
        }
        table[i] = NULL;
    }
    return;
}
#endif
