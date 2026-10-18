# Evaluating Retrieval

## Relevance judgments

Retrieval can only be measured when the relevant passages for each test question are known. A common practice is to write a set of questions, mark which passages contain the answer, and compare each retrieval result against those labels.

## Precision at k

Precision@k is the number of relevant chunks in the top k results divided by k. If 2 of the top 5 chunks are relevant, Precision@5 is 0.4. Precision punishes noisy results.

## Recall at k

Recall@k is the number of relevant items found in the top k results divided by the total number of relevant items. If a question has 4 relevant passages and 2 of them appear in the top 5, Recall@5 is 0.5. Recall rewards finding all the evidence, which matters for questions that need several passages.

## Mean reciprocal rank

The reciprocal rank of a query is 1 divided by the rank of the first relevant result, or 0 if none is found. If the first relevant chunk is at rank 3, the reciprocal rank is one third. Mean reciprocal rank (MRR) is the average of this value over all queries and shows how early the first useful passage appears.

## Evaluating generated answers

Retrieval metrics do not show whether the final answer is correct. Answer correctness should be compared with a written reference answer, faithfulness should check that each statement is supported by the retrieved context, and unanswerable questions should be scored by whether the system abstains. Using a language model as the judge is convenient but is not objective proof, because the judge can share the blind spots of the system being judged.
