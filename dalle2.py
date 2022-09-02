#forked from  ezzcodeezzlife/dalle2-in-python (https://github.com/ezzcodeezzlife/dalle2-in-python)

import json
import os
import requests
import time
import urllib
import urllib.request

from pathlib import Path

class Dalle2():
    def __init__(self, bearer):
        self.bearer = bearer
        self.batch_size = 4
        self.inpainting_batch_size = 3
        self.task_sleep_seconds = 3

    def generate(self, prompt):
        body = {
            "task_type": "text2im",
            "prompt": {
                "caption": prompt,
                "batch_size": self.batch_size,
            }
        }

        return self.get_task_response(body)

    def generate_and_download(self, prompt, image_dir=os.getcwd()):
        generations = self.generate(prompt)
        if not generations:
            return None
        elif generations == "failure":
            print("Failure!")
            return "failure"
        elif generations == "violation":
            print("Violation!")
            return "violation"
        else:
            return self.download(generations, image_dir)

    def get_task_response(self, body):
        url = "https://labs.openai.com/api/labs/tasks"
        headers = {
            'Authorization': "Bearer " + self.bearer,
            'Content-Type': "application/json",
        }
        count = 0
        for request in range(3):
            response = requests.post(url, headers=headers, data=json.dumps(body))
            if response.status_code != 200:
                count += 1
                if count == 3:
                    print(response.text)
                    return "failure"
                else:
                    time.sleep(10)
            elif response.status_code == 200:
                break

        data = response.json()
        print(f"✔️ Task created with ID: {data['id']}")
        print("⌛ Waiting for task to finish...")

        while True:
            count = 0
            url = f"https://labs.openai.com/api/labs/tasks/{data['id']}"
            for get_response in range(3):
                try:
                    response = requests.get(url, headers=headers)
                    data = response.json()
                    break
                except:
                    count += 1
                    if count == 3:
                        return "failure"
                    time.sleep(10)
            if not response.ok:
                print(f"Request failed with status: {response.status_code}, data: {response.json()}")
                return "failure"
            if data["status"] == "failed":
                print(f"Task failed: {data['status_information']}")
                return "failure"
            if data["status"] == "rejected":
                print(f"Task rejected: {data['status_information']}")
                return "violation"
            if data["status"] == "succeeded":
                print("🙌 Task completed!")
                return data["generations"]["data"]
            time.sleep(self.task_sleep_seconds)

    def download(self, generations, image_dir=os.getcwd()):
        if not generations:
            raise ValueError("generations is empty!")

        file_paths = []
        for generation in generations:
            image_url = generation["generation"]["image_path"]
            file_path = Path(image_dir, generation['id']).with_suffix('.png')
            file_paths.append(str(file_path))
            urllib.request.urlretrieve(image_url, file_path)
            print(f"✔️ Downloaded: {file_path}")

        return file_paths
