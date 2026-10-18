# Text Chunking Strategies

## Why documents are chunked

Embedding models and language models have limited input length, and a single vector for a whole document blurs many topics together. Splitting a document into chunks lets the retriever return only the passage that matters. Chunking therefore directly controls both retrieval precision and the amount of context passed to the generator.

## Fixed-size chunking

Fixed-size chunking cuts text every N characters or tokens. It is simple and predictable, but it can cut sentences in half and separate a statement from its explanation. Sentence-aware chunking packs whole sentences into a chunk until a size limit is reached, which keeps statements intact at the cost of slightly uneven chunk lengths.

## Chunk overlap

Overlap repeats the end of one chunk at the start of the next one. For small question-answering corpora, a chunk size of roughly 400 to 800 characters with an overlap of 10 to 20 percent is a common starting point. Overlap reduces the chance that an answer is split across a boundary, but it increases the number of vectors stored and can return near-duplicate chunks in the top-k results.

## Trade-offs between small and large chunks

Small chunks give precise matches and compact prompts, but they may lack the surrounding context needed to answer. Large chunks keep more context but dilute the embedding and waste prompt space on irrelevant sentences. There is no universally best size; the right value should be chosen by measuring retrieval quality on questions with known relevant passages.

## Metadata to keep

Each chunk should carry its source filename, page number when the format has pages, the section heading, and a stable chunk identifier. This metadata is what makes source citations possible later in the pipeline.
