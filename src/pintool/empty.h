#include <iostream>
#include <fstream>
#include <stdlib.h>
#include "pin.H"

#include "utils/fn_bound.h"
#include "utils/plt.h"
#include "utils/lib.h"

/* Out file to store results */
ofstream empty_ofile; 

/* Handler called at the end of the execution */
void empty_over(INT32 code, void *v, float elapsed) {
    empty_ofile << elapsed << endl;
    /* Close the log file */
    empty_ofile.close();
}

void empty_init(string pgm, string odir) {
    empty_ofile.open((odir + pgm + "_pempty.txt").c_str());
}

