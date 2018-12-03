#include <iostream>
#include <fstream>
#include <stdlib.h>
#include <list>
#include "pin.H"

typedef struct call_entry {
    ADDRINT calladdr;
    ADDRINT retaddr;
    ADDRINT rsp;
    struct call_entry *next;
} call_entry_t;

call_entry_t *CALL_STACK = NULL;

void cs_call(ADDRINT calladdr, ADDRINT retaddr, ADDRINT rsp) {
    call_entry_t *c = (call_entry_t *) malloc(sizeof(call_entry));
    c->calladdr = calladdr;
    c->retaddr = retaddr;
    c->rsp = rsp;
    c->next = CALL_STACK;
    CALL_STACK = c;
    return;
}

void cs_flush(call_entry_t *c) {
    call_entry_t *tmp;
    while (CALL_STACK && CALL_STACK != c) {
        tmp = CALL_STACK;
        CALL_STACK = CALL_STACK->next;
        free(tmp);
    }
}

void cs_ret(fn_bound_t **table, ADDRINT rip, ADDRINT addr) {
    call_entry_t *senti = CALL_STACK;
    while (senti) {
        if (senti->retaddr == addr) {
            /* Add return point to the function structure */
            fn_add_retaddr(table, senti->calladdr, rip);
            /* Flush the top of the call stack until senti (included) */
            cs_flush(senti->next);
            return;
        }
        senti = senti->next;
    }
    return;
}

call_entry_t *cs_find(ADDRINT addr) {
    call_entry_t *senti = CALL_STACK;
    while (senti) {
        if (senti->retaddr == addr) {
            return senti;
        }
        senti = senti->next;
    }
    return NULL;
}

call_entry_t *cs_top(void) {
    return CALL_STACK;
}
