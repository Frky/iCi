#ifndef __LIB_H__
#define __LIB_H__

#include "pin.H"

BOOL is_lib(ADDRINT addr) {
    PIN_LockClient();
    IMG img = IMG_FindByAddress(addr);
    PIN_UnlockClient();
    return (!IMG_Valid(img) || !IMG_IsMainExecutable(img));
}

#endif
