# to run this file you need model.onnx_data on the assets/onnx folder or you can obtain it from here.: https://huggingface.co/onnx-community/embeddinggemma-300m-ONNX/tree/main/onnx
import asyncio
import os
from typing import List

import numpy as np

# import onnxruntime as ort
from transformers import AutoTokenizer

BASE_DIR = os.path.dirname(__file__)

TOKENIZER_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "assets", "tokenizer"))

# MODEL_DIR = os.path.abspath(
#     os.path.join(BASE_DIR, "..", "assets", "onnx", "model.onnx")
# )


class EmbeddingModel:
    def __init__(self):
        # print(TOKENIZER_DIR)
        self.tokenizer = AutoTokenizer.from_pretrained(
            TOKENIZER_DIR, local_files_only=True
        )

        # sess_options = ort.SessionOptions()
        # providers = ["CPUExecutionProvider"]
        #
        # self.session = ort.InferenceSession(
        #     MODEL_DIR, sess_options, providers=providers
        # )
        #
        # self.input_names = [inp.name for inp in self.session.get_inputs()]
        # self.output_names = [out.name for out in self.session.get_outputs()]

    # def _run_sync(
    #     self, input_ids: np.ndarray, attention_mask: np.ndarray
    # ) -> List[float]:
    #     inputs = {}
    #
    #     if "input_ids" in self.input_names:
    #         inputs["input_ids"] = input_ids
    #     else:
    #         inputs[self.input_names[0]] = input_ids
    #
    #     if "attention_mask" in self.input_names:
    #         inputs["attention_mask"] = attention_mask
    #     elif len(self.input_names) > 1:
    #         inputs[self.input_names[1]] = attention_mask
    #
    #     outputs = self.session.run(self.output_names, inputs)
    #     emb = outputs[0]
    #
    #     if emb.ndim == 3:
    #         emb_vector = emb.mean(axis=1)[0]
    #     elif emb.ndim == 2:
    #         emb_vector = emb[0]
    #     else:
    #         emb_vector = np.asarray(emb).flatten()
    #
    #     return emb_vector.astype(float).tolist()

    async def embed_text(self, text: str, max_length: int = 512) -> List[float]:

        encoded = self.tokenizer(
            text,
            return_tensors="np",
            truncation=True,
            padding="longest",
            max_length=max_length,
        )

        input_ids = encoded["input_ids"].astype(np.int64)
        attention_mask = encoded.get("attention_mask", np.ones_like(input_ids)).astype(
            np.int64
        )

        # loop = asyncio.get_event_loop()
        # vector = await loop.run_in_executor(
        #     None, self._run_sync, input_ids, attention_mask
        # )
        # return vector
        return input_ids.flatten().tolist()


embedding_model = EmbeddingModel()


async def test_tokenizer():
    text = "What does the company telll about moonlighting"
    tokens = await embedding_model.embed_text(text)
    print("Tokenized text:", tokens)
