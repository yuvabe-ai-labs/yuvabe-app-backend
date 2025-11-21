import os
import numpy as np
from typing import List
import onnxruntime as ort
from transformers import AutoTokenizer
from huggingface_hub import hf_hub_download

MODEL_ID = "onnx-community/embeddinggemma-300m-ONNX"

class EmbeddingModel:
    def __init__(self):
        print("Loading tokenizer…")
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

        print("Downloading ONNX model files…")

        self.model_path = hf_hub_download(
            repo_id=MODEL_ID,
            filename="onnx/model.onnx"
        )
        self.data_path = hf_hub_download(
            repo_id=MODEL_ID,
            filename="onnx/model.onnx_data"
        )

        model_dir = os.path.dirname(self.model_path)

        print("Creating inference session…")
        self.session = ort.InferenceSession(
            self.model_path,
            providers=["CPUExecutionProvider"],
        )

        self.input_names = [i.name for i in self.session.get_inputs()]
        self.output_names = [o.name for o in self.session.get_outputs()]

    async def embed_text(self, text: str, max_length=512) -> List[float]:

        encoded = self.tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors="np",
        )

        input_ids = encoded["input_ids"].astype(np.int64)
        attention_mask = encoded["attention_mask"].astype(np.int64)

        outputs = self.session.run(
            self.output_names,
            {
                self.input_names[0]: input_ids,
                self.input_names[1]: attention_mask,
            },
        )
        last_hidden = outputs[0]

        mask = attention_mask[..., None]
        pooled = (last_hidden * mask).sum(axis=1) / mask.sum(axis=1)

        vec = pooled[0]

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.tolist()


embedding_model = EmbeddingModel()
