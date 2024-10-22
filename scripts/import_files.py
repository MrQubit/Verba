import asyncio
import websockets
import json
import os
import base64

async def upload_file_via_websocket(file_path: str, ws_url: str, credentials: dict):
    file_id = os.path.basename(file_path)  # The file's name used as the file ID
    chunk_size = 2000  # Match the frontend chunk size (2000 bytes per chunk)
    total_size = os.path.getsize(file_path)
    total_chunks = (total_size + chunk_size - 1) // chunk_size  # Calculate total number of chunks

    async with websockets.connect(ws_url) as websocket:
        with open(file_path, "rb") as file:
            chunk_order = 0

            while chunk := file.read(chunk_size):
                chunk_order += 1
                is_last_chunk = chunk_order == total_chunks

                # Encode the binary chunk into Base64 for transmission
                encoded_chunk = base64.b64encode(chunk).decode('utf-8')

                # Create the batch data payload as per the server's `DataBatchPayload` structure
                batch_data = {
                    "credentials": credentials,  # Including credentials
                    "fileID": file_id,  # File ID based on filename
                    "order": chunk_order,  # Current chunk number
                    "total": total_chunks,  # Total number of chunks
                    "chunk": encoded_chunk,  # Base64 encoded chunk (string)
                    "isLastChunk": is_last_chunk  # Flag to indicate the last chunk
                }

                # Send the current chunk as JSON
                await websocket.send(json.dumps(batch_data))
                print(f"Sent chunk {chunk_order}/{total_chunks}")

                try:
                    # Set a timeout for the response from the server
                    response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    print(f"Response from server after chunk {chunk_order}: {response}")
                except asyncio.TimeoutError:
                    print(f"Warning: No response from server after sending chunk {chunk_order}. Continuing...")

                if is_last_chunk:
                    print(f"All chunks sent for file {file_id}. Upload completed.")

# Example usage
credentials = {
    "deployment": "Custom",
    "url": "localhost",
    "key": ""
}

file_path = "C:/verba_test/test_pdf_5.pdf"  # Replace with your file path
ws_url = "ws://localhost:8000/ws/import_files"  # Adjust based on your server configuration

# Run the WebSocket client
asyncio.get_event_loop().run_until_complete(upload_file_via_websocket(file_path, ws_url, credentials))
