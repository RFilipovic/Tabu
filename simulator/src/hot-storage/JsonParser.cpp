#include "ParsedBuffers.h"
#include "UntilDueContainer.h"
#include <nlohmann/json.hpp>
#include <fstream>

void exportStateToJson(ParsedBuffers& parsed, const std::string& outputPath) {
    using json = nlohmann::json;

    json stateJson;

    // Add stack names
    stateJson["stacks"] = parsed.getStackNames();

    // Add containers
    json containersJson = json::array();
    const auto& stackNames = parsed.getStackNames();
    const auto& buffers = parsed.getBuffers();

    for (size_t i = 0; i < buffers.size(); ++i) {
        const std::string& stack = stackNames[i];
        for (const auto* container : buffers[i]->getContainers()) {
            const auto* udc = dynamic_cast<const UntilDueContainer*>(container);
            if (udc) {
                json containerJson;
                containerJson["id"] = udc->getId();
                containerJson["stack"] = stack;
                containerJson["minutes"] = udc->getUntilDue().getMinutes();
                containerJson["seconds"] = udc->getUntilDue().getSeconds();
                containersJson.push_back(containerJson);
            }
        }
    }

    stateJson["containers"] = containersJson;

    // Write to file
    std::ofstream outFile(outputPath);
    outFile << stateJson.dump(2); // pretty print with indent = 2
    outFile.close();
}
