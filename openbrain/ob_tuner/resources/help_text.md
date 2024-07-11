# 🚀 Agent Configurations
## 📲 Loading an Agent's Settings
Choose an agent by selecting a `profile_name` and a `client_id`. The agent's settings will be loaded into the form. You can then modify the settings and save them. You can also reset the agent to its initial state. This will load the agent's configuration into Gradio for inspection and modification.

## 💽 Saving an Agent's Settings
Once all required agent fields are filled out, click the **Save** button to save the agent's settings. The settings will be saved to the DynamoDB database. You can then load the agent's settings at a later time.

> ⚠️ **Do not modify AgentConfigs in the public or leadmo client_id's, they may be overwritten by devops pipelines.**

# 🌍 Context
Some tools require some information from the incoming API call. You can send a contact's personal information like `firstName`, `lastName`, `dob`, etc. in your request (for LeadMomentum, see the custom webhook message). This information is the context for the conversation.

The context section below simulates the leadmo workflow by calling the leadmo API with the values seen here, and then replacing values such as `contactId` with the returned values. Be aware that the default customerId certainly doesn't exist in the leadmo database, so tools such as `leadmo_update_contact` will fail until a contact is created (maybe by using the `leadmo_create_contact` tool).

# 📆 Events
Events either gather information or perform an action. Action events are replayable, best-effort, ephemeral functions. Tools that perform an action, such as updating a Lead Momentum contact create action events. Events are stored in a DynamoDB table and can be retrieved for debugging purposes. You can see if your event triggered using the Action Events tab.

# 🔧 Available Tools
Tools are functions that can be called by the agent. They can be used to gather information or perform an action. Tools are defined in the `openbrain/tools` directory. You can see the available tools and their descriptions in the Available Tools tab.

# 🤖 Debugging Agents
The Agent Debugging tab shows the cloudwatch logs from the agent. If you encounter any issues, you can copy the logs and send them to the Sam for debugging.

# 🐛 Debugging Gradio Interface
The Debug tab shows the logs from the program. If you encounter any issues, you can copy the logs and send them to the Sam for debugging.
