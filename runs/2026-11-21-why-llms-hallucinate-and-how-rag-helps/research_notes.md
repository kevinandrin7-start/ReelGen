# Research notes: Why LLMs hallucinate, and how RAG helps

## Definition
- Hallucination: a model confidently generates an answer that isn't true (OpenAI).
- IBM: a specific type of mistake where the system confidently generates false or fabricated information.

## Why it happens
- LLMs predict the next token from prior context; they optimize for plausibility, not correctness, and don't "know" what's true (IBM).
- Flawed/incomplete training data and lack of grounding lead to plausible but false outputs, even fake links (Google Cloud).
- OpenAI (Sept 2025 paper, arXiv 2509.04664): training and evaluation reward guessing over admitting uncertainty. Birthday example: guess = 1/365 chance, "I don't know" = 0 points.

## Real example
- Mata v. Avianca (S.D.N.Y., June 2023): lawyers fined $5,000 for submitting non-existent cases fabricated by ChatGPT; ChatGPT even claimed one fake case "does indeed exist".

## How RAG helps
- RAG connects the model to a curated knowledge base; it retrieves relevant passages and answers from them, often with citations (IBM).
- Shuster et al. 2021 (arXiv 2104.07567): retrieval augmentation substantially reduces knowledge hallucination in chatbots (human evaluations).
- Reduces, does not eliminate, hallucinations (NVIDIA).

## Sources
- https://openai.com/index/why-language-models-hallucinate/
- https://arxiv.org/abs/2509.04664
- https://www.ibm.com/think/topics/ai-hallucinations
- https://cloud.google.com/discover/what-are-ai-hallucinations
- https://arxiv.org/abs/2104.07567
- https://blogs.nvidia.com/blog/what-is-retrieval-augmented-generation/
- https://law.justia.com/cases/federal/district-courts/new-york/nysdce/1:2022cv01461/575368/54/
