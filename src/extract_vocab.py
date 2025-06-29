import os
import glob
import json
import shutil
import time

from src.utils.prompt import extract_vocabs
from src.utils.api import Gemini


INPUT_PATH = "data_tmp.txt"
CONTENT_SIZE = 4000 * 4  # 4000 tokens * 4 characters per token
OUTPUT_DIR = "output"


if __name__ == "__main__":
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        blocks = f.read().split("\n\n")

    tmp_dir = f"{OUTPUT_DIR}/.tmp_vocab"
    os.makedirs(tmp_dir, exist_ok=True)
    model = Gemini("gemini-2.0-flash-lite")

    # Save the vocabularies in chunks
    content, block_i, chunk_i = "", 0, 0
    while block_i < len(blocks) and len(content) < CONTENT_SIZE:
        content += blocks[block_i] + "\n\n"
        block_i += 1
        
        if len(content) >= CONTENT_SIZE or block_i == len(blocks):
            print(f"Processing chunk: {chunk_i}")

            prompt = extract_vocabs.strip(" \n").replace("{{ vocabularies }}", content)
            resp = model.run(prompt=prompt)
            time.sleep(10)  # Sleep to avoid rate limits
            
            out = resp.replace("```", "").replace("json", "").strip("\n")
            open(f"{tmp_dir}/vocab_{chunk_i}.txt", "w").write(out)
            try:
                json.dump(
                    json.loads(out),
                    open(f"{tmp_dir}/vocab_{chunk_i}.json", "w", encoding="utf-8"),
                    ensure_ascii=False,
                    indent=4
                )
            except Exception as e:
                print(f"Error at chunk {chunk_i}: {e}")
            
            content = ""
            chunk_i += 1

    # Merge all vocab chunks
    merged_vocabs = []
    for json_path in glob.glob(f"{tmp_dir}/vocab_*.json"):
        with open(json_path, "r", encoding="utf-8") as f:
            vocabs = json.load(f)
            merged_vocabs.extend(vocabs)
    
    # remove temp directory recursively by shutil
    shutil.rmtree(tmp_dir)

    # Save merged vocabularies
    with open(f"{OUTPUT_DIR}/vocab.json", "w", encoding="utf-8") as f:
        json.dump(merged_vocabs, f, ensure_ascii=False, indent=4)
    