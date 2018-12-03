#ifndef __PLT_H__
#define __PLT_H__

#include "pin.H"

typedef struct plt_bound {
    ADDRINT start;
    ADDRINT end;
    struct plt_bound *next;
} plt_bound_t;

plt_bound_t *PLT;
plt_bound_t *PLTGOT;

VOID add_plt(ADDRINT start, ADDRINT end) {
    /* First look for start addr in linked list */
    plt_bound_t *senti = PLT;
    while (senti) {
        if (senti->start == start)
            return;
        senti = senti->next;
    }
    plt_bound_t *p = (plt_bound_t *) malloc(sizeof(plt_bound_t));
    p->start = start;
    p->end = end; 
    p->next = PLT;
    PLT = p;
    return;
}

VOID add_pltgot(ADDRINT start, ADDRINT end) {
    plt_bound_t *p = (plt_bound_t *) malloc(sizeof(plt_bound_t));
    p->start = start;
    p->end = end; 
    p->next = PLTGOT;
    PLTGOT = p;
    return;
}

BOOL is_plt_or_pltgot(ADDRINT addr) {
    plt_bound_t *senti = PLT;
    while (senti) {
        if (senti->start <= addr && addr <= senti->end)
            return true;
        senti = senti->next;
    }
    senti = PLTGOT;
    while (senti) {
        if (senti->start <= addr && addr <= senti->end)
            return true;
        senti = senti->next;
    }
    return false;
}

BOOL jmp_from_plt_or_pltgot(INS ins) {
    return (INS_Category(ins) == XED_CATEGORY_UNCOND_BR
            && is_plt_or_pltgot(INS_Address(ins)));
}

#endif
