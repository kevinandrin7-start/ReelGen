# Research notes: What is RAG?

- Definition (AWS): RAG optimizes LLM output so it references an authoritative knowledge base outside its training data before generating a response, without retraining.
- Problem (AWS): training data is static -> knowledge cut-off; LLMs can present false or out-of-date info.
- How it works (AWS, NVIDIA): embed documents into a vector database; embed the query; match and retrieve relevant passages; augment the prompt; LLM generates answer, can cite sources. Keep the index updated.
- Origin (arXiv, NVIDIA): Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", submitted 22 May 2020; FAIR, UCL, NYU. Non-parametric memory = dense vector index of Wikipedia. More specific, diverse and factual output than parametric-only baseline.
- Trust (NVIDIA): sources like footnotes; reduces hallucination risk. Faster and cheaper than retraining; sources can be hot-swapped.
- Analogy (NVIDIA): judge + court clerk fetching precedents from a law library. Also: open-book exam.
- Misconceptions: doesn't retrain the model; reduces but doesn't eliminate hallucinations.

## Sources
- https://blogs.nvidia.com/blog/what-is-retrieval-augmented-generation/
- https://aws.amazon.com/what-is/retrieval-augmented-generation/
- https://arxiv.org/abs/2005.11401
