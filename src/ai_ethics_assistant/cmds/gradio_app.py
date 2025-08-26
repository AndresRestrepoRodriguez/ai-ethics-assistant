#!/usr/bin/env python3
"""
Gradio UI for AI Ethics Assistant
Provides a user-friendly chat interface for testing the RAG system
"""

import json
import logging
import sys

import gradio as gr
import httpx

from ai_ethics_assistant.configuration import Config

logger = logging.getLogger(__name__)


class GradioRAGInterface:
    """Gradio interface for the AI Ethics Assistant RAG system"""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url

    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface"""

        def sync_chat_wrapper(message, history, stream_enabled, top_k):
            """Synchronous wrapper for async chat function"""
            # Use sync HTTP client instead of async to avoid event loop issues
            import httpx

            if not message.strip():
                return "", history

            new_history = history + [[message, ""]]

            try:
                with httpx.Client(timeout=60.0) as client:
                    if stream_enabled:
                        # Use streaming with sync client
                        with client.stream(
                            "POST",
                            f"{self.api_base_url}/api/v1/chat",
                            json={"query": message, "stream": True, "top_k": top_k},
                        ) as response:
                            if response.status_code == 200:
                                response_text = ""
                                for line in response.iter_lines():
                                    if line.startswith("data: "):
                                        try:
                                            data = json.loads(line[6:])
                                            if data.get("type") == "chunk":
                                                response_text += data.get("content", "")
                                            elif data.get("type") == "end":
                                                break
                                        except json.JSONDecodeError:
                                            continue
                                new_history[-1][1] = response_text
                            else:
                                new_history[-1][1] = (
                                    f"API Error: {response.status_code}"
                                )
                    else:
                        # Non-streaming request
                        response = client.post(
                            f"{self.api_base_url}/api/v1/chat",
                            json={"query": message, "stream": False, "top_k": top_k},
                        )
                        if response.status_code == 200:
                            result = response.json()
                            new_history[-1][1] = result.get(
                                "answer", "No response received"
                            )
                        else:
                            new_history[-1][1] = f"API Error: {response.status_code}"
            except Exception as e:
                new_history[-1][1] = f"Connection Error: {str(e)}"

            return "", new_history

        def sync_health_check():
            """Synchronous wrapper for health check"""
            import httpx

            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(f"{self.api_base_url}/api/v1/rag/health")
                    if response.status_code == 200:
                        health_data = response.json()
                        overall_status = health_data.get("overall", "unknown")

                        if overall_status == "healthy":
                            return "✅ RAG System: All components healthy"
                        elif overall_status == "degraded":
                            return "⚠️ RAG System: Some components unhealthy"
                        else:
                            error = health_data.get("error", "Unknown error")
                            return f"❌ RAG System: Unhealthy - {error}"
                    else:
                        return f"❌ API Connection: Error {response.status_code}"
            except Exception as e:
                return f"❌ API Connection: Failed to connect - {str(e)}"

        def sync_status_check():
            """Synchronous wrapper for status check"""
            import httpx

            try:
                with httpx.Client(timeout=10.0) as client:
                    response = client.get(f"{self.api_base_url}/api/v1/status")
                    if response.status_code == 200:
                        status_data = response.json()
                        services = status_data.get("services", {})
                        dev_mode = status_data.get("dev_mode", False)

                        status_text = (
                            f"System Status: {status_data.get('status', 'unknown')}\n"
                        )
                        status_text += (
                            f"Development Mode: {'Yes' if dev_mode else 'No'}\n"
                        )
                        status_text += f"API: {services.get('api', 'unknown')}\n"
                        status_text += (
                            f"Vector DB: {services.get('vector_db', 'unknown')}\n"
                        )
                        status_text += f"LLM: {services.get('llm', 'unknown')}"

                        return status_text
                    else:
                        return f"Failed to get status: {response.status_code}"
            except Exception as e:
                return f"Failed to connect: {str(e)}"

        with gr.Blocks(
            title="AI Ethics Assistant",
            theme="soft",
        ) as interface:
            gr.Markdown("# 🤖 AI Ethics Assistant")
            gr.Markdown(
                "Ask questions about AI policy, ethics, governance, and regulation based on curated documents."
            )

            with gr.Tab("Chat"):
                with gr.Row():
                    with gr.Column(scale=4):
                        chatbot = gr.Chatbot(
                            height=500,
                            placeholder="Hi! I'm your AI Ethics Assistant. Ask me about AI policy, ethics, governance, or regulations.",
                            show_label=False,
                        )

                        with gr.Row():
                            msg = gr.Textbox(
                                placeholder="Ask about AI ethics, policy, or governance...",
                                show_label=False,
                                scale=4,
                            )
                            send_btn = gr.Button("Send", scale=1, variant="primary")
                            clear_btn = gr.Button("Clear", scale=1)

                    with gr.Column(scale=1, min_width=250):
                        gr.Markdown("### Settings")

                        stream_enabled = gr.Checkbox(
                            label="Enable Streaming",
                            value=True,
                            info="Stream responses in real-time",
                        )

                        top_k = gr.Slider(
                            minimum=1,
                            maximum=10,
                            value=5,
                            step=1,
                            label="Documents to Retrieve",
                            info="Number of relevant documents to use for context",
                        )

                        gr.Markdown("### Example Questions")
                        gr.Markdown("""
                        - What are the key principles of AI ethics?
                        - How should AI systems be governed?
                        - What are the main AI regulation frameworks?
                        - What is algorithmic accountability?
                        - How can we ensure AI fairness?
                        """)

                # Handle message submission
                def submit_message(message, history, stream_enabled, top_k):
                    return sync_chat_wrapper(message, history, stream_enabled, top_k)

                msg.submit(
                    submit_message,
                    [msg, chatbot, stream_enabled, top_k],
                    [msg, chatbot],
                )

                send_btn.click(
                    submit_message,
                    [msg, chatbot, stream_enabled, top_k],
                    [msg, chatbot],
                )

                clear_btn.click(lambda: (None, []), outputs=[msg, chatbot])

            with gr.Tab("System Status"):
                gr.Markdown("### System Health")

                with gr.Row():
                    health_output = gr.Textbox(
                        label="RAG System Health", lines=2, interactive=False
                    )
                    health_btn = gr.Button("Check Health", variant="secondary")

                health_btn.click(sync_health_check, outputs=health_output)

                gr.Markdown("### System Information")

                with gr.Row():
                    status_output = gr.Textbox(
                        label="System Status", lines=6, interactive=False
                    )
                    status_btn = gr.Button("Get Status", variant="secondary")

                status_btn.click(sync_status_check, outputs=status_output)

                # Auto-load status on tab load
                interface.load(sync_health_check, outputs=health_output)
                interface.load(sync_status_check, outputs=status_output)

            gr.Markdown("""
            ### About
            This AI Ethics Assistant uses Retrieval-Augmented Generation (RAG) to answer questions about AI policy and ethics.
            The system retrieves relevant information from curated documents and generates contextual responses using Mistral-7B.
            """)

        return interface


def main():
    """Main function to run the Gradio app"""
    import os

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    config = Config()
    # Use BACKEND_URL env var if set (for Docker), otherwise localhost
    api_url = os.environ.get("BACKEND_URL", "http://localhost:8000")

    if config.dev_mode:
        logger.info("Running in development mode")

    logger.info(f"Connecting to API at: {api_url}")

    rag_interface = GradioRAGInterface(api_base_url=api_url)

    # Check API connectivity
    with httpx.Client(timeout=10.0) as client:
        try:
            response = client.get(f"{api_url}/api/v1/rag/health")
            if response.status_code == 200:
                logger.info("API Health Check: Successfully connected")
            else:
                logger.warning(f"API Health Check: Status {response.status_code}")
        except Exception as e:
            logger.warning(f"API Health Check: Failed to connect - {e}")

    # Create and launch interface
    interface = rag_interface.create_interface()

    logger.info("Launching Gradio interface...")
    logger.info("Open http://localhost:7860 in your browser")

    # Launch with public sharing disabled by default
    interface.launch(
        server_name="0.0.0.0",  # Always bind to all interfaces for Docker
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False,
    )


if __name__ == "__main__":
    main()
