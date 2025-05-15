#include <iostream>

#include "HotStorageSimulator.h"

int main(){

    ParsedBuffers *data = new ParsedBuffers("ulaz.txt");
    Crane *crane = new SingleContainerCrane("CRANE", data->getStackNames());
    Printer *printer = new Printer(*data, *crane);

    HotStorageSimulator simulator(*printer);

    simulator.simulate();

    return 0;
}