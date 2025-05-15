#include "Crane.h"

Crane::Crane(const std::string &name, const std::vector<std::string> &stackNames)
    : name(name), stackNames(stackNames) {
        aboveStack = stackNames.at(0);
        aboveStackIndex = 0;
    }

std::string Crane::getName() const
{
    return name;
}

void Crane::setName(const std::string &newName)
{
    name = newName;
}

std::string Crane::getAboveStack() const
{
    return aboveStack;
}

void Crane::setAboveStack(std::string newAboveStack)
{
    aboveStack = newAboveStack;
}

int Crane::getAboveStackIndex() const{
    return aboveStackIndex;
}

void Crane::setAboveStackIndex(int index){
    aboveStackIndex = index;
    setAboveStack(stackNames.at(index));
}