#!/usr/bin/env python
from dotenv import load_dotenv
from typing import Dict
from naptha_sdk.schemas import AgentRunInput
from naptha_sdk.user import sign_consumer_id
from naptha_sdk.utils import get_logger
from generate_3d.schemas import InputSchema
import requests
import os

load_dotenv()

logger = get_logger(__name__)

# You can create your module as a class or function
class Generate3DModule:
    def __init__(self, module_run):
        self.module_run = module_run
        self.api_key = os.getenv('STABILITY_API_KEY')
        if not self.api_key:
            raise ValueError("STABILITY_API_KEY environment variable is not set")

    def image_to_3d(self, input_data):
        """Generate a 3D model from an input image using Stability AI API"""
        logger.info("Generating 3D model from input image")
        
        try:
            # Assuming input_data contains the path to the input image
            response = requests.post(
                "https://api.stability.ai/v2beta/3d/stable-fast-3d",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                },
                files={
                    "image": open(input_data, "rb")
                },
                data={},
            )

            if response.status_code == 200:
                output_path = "output_3d_model.glb"
                with open(output_path, 'wb') as file:
                    file.write(response.content)
                return f"3D model generated successfully and saved to {output_path}"
            else:
                error_msg = str(response.json())
                logger.error(f"Failed to generate 3D model: {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Error generating 3D model: {str(e)}")
            raise

# Default entrypoint when the module is executed
def run(module_run: Dict):
    module_run = AgentRunInput(**module_run)
    module_run.inputs = InputSchema(**module_run.inputs)
    basic_module = Generate3DModule(module_run)
    method = getattr(basic_module, module_run.inputs.func_name, None)
    return method(module_run.inputs.func_input_data)

if __name__ == "__main__":
    import asyncio
    from naptha_sdk.client.naptha import Naptha
    from naptha_sdk.configs import setup_module_deployment
    import os

    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        raise ValueError("PRIVATE_KEY environment variable is not set")

    naptha = Naptha()
    
    # Make sure the signature is properly generated before creating the module_run
    consumer_id = naptha.user.id
    signature = sign_consumer_id(consumer_id, private_key)
    if not signature:
        raise ValueError("Failed to generate signature")

    deployment = asyncio.run(setup_module_deployment("agent", "generate_3d/configs/deployment.json", node_url = os.getenv("NODE_URL")))

    input_params = {
        "func_name": "image_to_3d",
        "func_input_data": "./input_image.png",
    }

    module_run = {
        "inputs": input_params,
        "deployment": deployment,
        "consumer_id": consumer_id,
        "signature": signature  # Using the validated signature
    }

    response = run(module_run)
    print("Response: ", response)
    