import argparse
import json

import datasets

from src.utils import call_llm


def classify_paper(paper):
    system_prompt = """The user will provide the title, abstract of a paper, please decide which category the paper is belonging among the following list: ["IoT Security Technologies","IoT Security Evaluation","Model Attacks","Model Defenses","Other Model-Related Security Research","Research on Attacks and Defenses in Federated Learning Scenarios","Homomorphic Encryption Technology","Secure Multi-Party Computation","Zero-Knowledge Proof","Differential Privacy","Dynamic Vulnerability Detection Methods","Static Vulnerability Detection Methods","Web Vulnerability Detection","Mobile Vulnerability Detection","Large Model Security and Assisted Security","Large Model Security","Large Model-Assisted Security"], if none of the categories is suitable, output other, return the output in json format. 

    EXAMPLE INPUT: 
    {'title': 'Securely Training Decision Trees Efficiently',
    'abstract': 'Decision trees are an important class of supervised learning algorithms. When multiple entities contribute data to train a decision tree (e.g. for fraud detection in the financial sector), data privacy concerns necessitate the use of a privacy-enhancing technology such as secure multi-party computation (MPC) in order to secure the underlying training data. Prior state-of-the-art (Hamada et al. [18]) construct an MPC protocol for decision tree training with a communication of O( ℎ𝑚𝑁 log 𝑁 ) , when building a decision tree of height ℎ for a training dataset of 𝑁 samples, each having 𝑚 attributes. In this work, we significantly reduce the communication complexity of secure decision tree training. We construct a protocol with communication complexity O( 𝑚𝑁 log 𝑁 + ℎ𝑚𝑁 + ℎ𝑁 log 𝑁 ) , thereby achieving an improvement of ≈ min ( ℎ,𝑚, log 𝑁 ) over [18]. At the core of our technique is an improved protocol to regroup sorted private elements further into additional groups (according to a flag vector) while maintaining their relative ordering. We implement our protocol in the MP-SPDZ framework [1, 22] and show that it requires 10 × lesser communication and is 9 × faster than [18].'}

    EXAMPLE JSON OUTPUT:
    {
        "type": "Secure Multi-Party Computation"
    }
    """

    user_prompt = f"{{'title': {paper['title']}, 'abstract': {paper['abstract']}}}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = call_llm(
        messages=messages,
        response_format={"type": "json_object"},
    )

    return json.loads(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", help="Path to the dataset")
    parser.add_argument("--output", help="Path to the output")
    args = parser.parse_args()

    ds = datasets.load_from_disk(args.dataset)
    new_ds = ds.map(classify_paper, num_proc=10)
    new_ds.save_to_disk(args.output)


if __name__ == "__main__":
    main()
