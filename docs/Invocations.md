The InvocationResponse is the standard respose Overmind will be sending back to you. It will include the following:
* invocation_id - UUID for identifying individual calls
* agent_id - unique ID assigned to your agents, see sections below on how to create new agents
* raw_input - that's the original input we've received
* processed_input - that's the input that was passed to an LLM. Depending on the input policies this can differ from the raw input.
* raw_output - that's the original output produced by LLM
* processed_output - that's the output that we've passed through the specified policies, it may differ from the raw output
* policy_result - any relevant results produced by the specified policies.
* business_id - your business id, at this moment we only support one business id per user
* created_at & updated_at - as per the name, inovcations aren't modifiable right now so updated at will always be None