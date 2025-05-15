#include <iostream>
#include <string>
#include <iomanip>

#include "UntilDueContainer.h"

UntilDue::UntilDue() {}

UntilDue::UntilDue(int minutes, int seconds) : minutes(minutes), seconds(seconds) {}

std::string UntilDue::toString() const {
    std::ostringstream oss;
    oss << std::setw(2) << std::setfill('0') << minutes << ":"
        << std::setw(2) << std::setfill('0') << seconds;
    return oss.str();
}

void UntilDue::setMinutes(int minutes){
    this->minutes = minutes;
}

int UntilDue::getMinutes(){
    return minutes;
}

void UntilDue::setSeconds(int seconds){
    this->seconds = seconds;
}

int UntilDue::getSeconds(){
    return seconds;
}

UntilDueContainer::UntilDueContainer() {}

UntilDueContainer::UntilDueContainer(const std::string &id, const UntilDue &untilDue)
    : Container(id), untilDue(untilDue) {}

void UntilDueContainer::displayDetails() const  {
    std::string combinedOutput = id + " " + untilDue.toString();

    std::cout << std::setw(11) << combinedOutput;
}

std::string UntilDueContainer::getDetails() const{
    return id + " " + untilDue.toString();
}

UntilDue UntilDueContainer::getUntilDue() const { return untilDue; }

void UntilDueContainer::setUntilDue(UntilDue &newUntilDue) { untilDue = newUntilDue; }

std::string UntilDueContainer::getId() const { return id; }