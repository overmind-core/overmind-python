#!/usr/bin/env python3
"""
Basic usage example for the Overmind Python client.
"""

from overmind_client import OvermindClient


def main():
    # Initialize the client with your credentials
    client = OvermindClient(
        overmind_api_key="your_overmind_api_key_here",
        openai_api_key="your_openai_api_key_here",
    )

    print("=== Overmind Python Client Example ===\n")

    # Example 1: Using OpenAI chat completions with dynamic access
    print("1. Using OpenAI chat completions:")
    try:
        response = client.openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello! What's 2 + 2?"}],
            agent_id="default_agent",
        )
        print(f"Response: {response.processed_output}")
        print(f"Invocation ID: {response.invocation_id}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 50 + "\n")

    # Example 2: Listing agents using sub-client
    print("2. Listing agents:")
    try:
        agents = client.agents.list()
        for agent in agents:
            print(f"- {agent.agent_id}: {agent.agent_description}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 50 + "\n")

    # Example 3: Creating a new agent using sub-client
    print("3. Creating a new agent:")
    try:
        new_agent = client.agents.create(
            {
                "agent_id": "example_agent",
                "agent_model": "gpt-4o",
                "agent_description": "An example agent for testing",
                "input_policies": ["reject_prompt_injection"],
                "output_policies": ["reject_irrelevant_answer"],
            }
        )
        print(f"Created agent: {new_agent.agent_id}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 50 + "\n")

    # Example 4: Listing policies using sub-client
    print("4. Listing policies:")
    try:
        policies = client.policies.list()
        for policy in policies:
            print(f"- {policy.policy_id}: {policy.policy_description}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 50 + "\n")

    # Example 5: Using the new agent with dynamic access
    print("5. Using the new agent:")
    try:
        response = client.openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Tell me a joke"}],
            agent_id="example_agent",
        )
        print(f"Response: {response.processed_output}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 50 + "\n")

    # Example 6: Managing invocations using sub-client
    print("6. Listing invocations for the example agent:")
    try:
        invocations = client.invocations.list("example_agent")
        for invocation in invocations:
            print(
                f"- Invocation {invocation.invocation_id}: {invocation.raw_output[:50]}..."
            )
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
