# Prediction Knowledge Directory

Place local policy and rules files for the intelligent prediction RAG module here.

Supported formats:
- `.txt`
- `.md`
- `.json`
- `.csv`
- `.docx`

Current retriever behavior:
- Recursively scans this directory
- Splits documents into text chunks
- Uses keyword scoring with the chat question and student risk context
- Injects top matches into `retrievedKnowledge`

Notes:
- `README.md` itself is ignored by the retriever
- If you later restore a folder like `研究生文件规定`, you can also add it to `PREDICTION_KNOWLEDGE_DIRS`
