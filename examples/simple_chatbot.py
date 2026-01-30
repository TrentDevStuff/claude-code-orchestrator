#!/usr/bin/env python3
"""
Simple Chatbot Example

Demonstrates:
- Interactive chatbot using Claude Code API
- Conversation history management
- Streaming responses (simulated)
- Error handling
- Usage statistics
"""

import sys
sys.path.append('..')

from client.claude_client import ClaudeClient, Model, BudgetExceededError, ClaudeAPIError


def main():
    """Run interactive chatbot."""
    print("=" * 60)
    print("Claude Code API - Simple Chatbot")
    print("=" * 60)
    print()
    print("Commands:")
    print("  /help   - Show this help")
    print("  /stats  - Show usage statistics")
    print("  /model  - Change model (haiku/sonnet/opus)")
    print("  /clear  - Clear conversation history")
    print("  /quit   - Exit chatbot")
    print()

    # Initialize client
    client = ClaudeClient(
        base_url="http://localhost:8080",
        project_id="chatbot-demo",
        timeout=60.0
    )

    # Check if API is running
    try:
        health = client.health()
        print(f"✓ Connected to API (version {health['version']})")
        print()
    except Exception as e:
        print(f"✗ Error: Could not connect to API")
        print(f"  Make sure the API is running: python main.py")
        print(f"  Error details: {e}")
        return

    # Conversation state
    conversation = []
    current_model = Model.AUTO
    total_cost = 0.0
    total_tokens = 0

    print(f"Current model: {current_model.value}")
    print()

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.startswith("/"):
                command = user_input[1:].lower()

                if command == "quit":
                    print()
                    print(f"Session summary:")
                    print(f"  Total cost: ${total_cost:.4f}")
                    print(f"  Total tokens: {total_tokens:,}")
                    print(f"  Messages: {len(conversation) // 2}")
                    print()
                    print("Goodbye!")
                    break

                elif command == "help":
                    print()
                    print("Commands:")
                    print("  /help   - Show this help")
                    print("  /stats  - Show usage statistics")
                    print("  /model  - Change model")
                    print("  /clear  - Clear conversation history")
                    print("  /quit   - Exit chatbot")
                    print()
                    continue

                elif command == "stats":
                    print()
                    stats = client.get_usage(period="month")
                    print(f"Usage statistics:")
                    print(f"  Project: {stats.project_id}")
                    print(f"  Period: {stats.period}")
                    print(f"  Total tokens: {stats.total_tokens:,}")
                    print(f"  Total cost: ${stats.total_cost:.4f}")

                    if stats.limit:
                        usage_pct = (stats.total_tokens / stats.limit) * 100
                        print(f"  Budget: {usage_pct:.1f}% used")
                        print(f"  Remaining: {stats.remaining:,} tokens")

                    print()
                    print(f"By model:")
                    for model_name, model_stats in stats.by_model.items():
                        print(f"  {model_name}: {model_stats['tokens']:,} tokens, ${model_stats['cost']:.4f}")
                    print()
                    continue

                elif command == "model":
                    print()
                    print("Available models:")
                    print("  1. auto   - Automatic selection (recommended)")
                    print("  2. haiku  - Fast and cheap")
                    print("  3. sonnet - Balanced")
                    print("  4. opus   - Most capable")
                    print()
                    choice = input("Select model (1-4): ").strip()

                    models = {
                        "1": Model.AUTO,
                        "2": Model.HAIKU,
                        "3": Model.SONNET,
                        "4": Model.OPUS
                    }

                    if choice in models:
                        current_model = models[choice]
                        print(f"✓ Model changed to: {current_model.value}")
                    else:
                        print("Invalid choice")
                    print()
                    continue

                elif command == "clear":
                    conversation = []
                    print()
                    print("✓ Conversation history cleared")
                    print()
                    continue

                else:
                    print(f"Unknown command: /{command}")
                    print("Type /help for available commands")
                    print()
                    continue

            # Add user message to conversation
            conversation.append({"role": "user", "content": user_input})

            # Build prompt with conversation history
            if len(conversation) <= 2:
                # First message - no history
                prompt = user_input
            else:
                # Include conversation context
                context = []
                for msg in conversation[:-1]:  # All messages except current
                    context.append(f"{msg['role']}: {msg['content']}")
                context.append(f"user: {user_input}")
                prompt = "\\n\\n".join(context)

            # Get response
            print("Claude: ", end="", flush=True)

            try:
                response = client.complete(
                    prompt=prompt,
                    model=current_model,
                    timeout=60.0
                )

                # Display response
                print(response.content)
                print()

                # Add to conversation
                conversation.append({"role": "assistant", "content": response.content})

                # Update statistics
                total_cost += response.cost
                total_tokens += response.usage.total_tokens

                # Show cost for this response
                print(f"[Model: {response.model}, Tokens: {response.usage.total_tokens}, Cost: ${response.cost:.6f}]")
                print()

            except BudgetExceededError:
                print("\\n\\n❌ Budget exceeded for this project!")
                print("Consider:")
                print("  - Using a cheaper model (/model → haiku)")
                print("  - Clearing history (/clear)")
                print("  - Checking usage (/stats)")
                print()

            except ClaudeAPIError as e:
                print(f"\\n\\n❌ API Error: {e.message}")
                print()

        except KeyboardInterrupt:
            print("\\n\\nInterrupted by user")
            print()
            choice = input("Really quit? (y/n): ").strip().lower()
            if choice == 'y':
                print()
                print(f"Session summary:")
                print(f"  Total cost: ${total_cost:.4f}")
                print(f"  Total tokens: {total_tokens:,}")
                print(f"  Messages: {len(conversation) // 2}")
                print()
                print("Goodbye!")
                break
            else:
                print()

        except Exception as e:
            print(f"\\n\\n❌ Unexpected error: {e}")
            print("Type /quit to exit or continue chatting")
            print()

    # Cleanup
    client.close()


if __name__ == "__main__":
    main()
