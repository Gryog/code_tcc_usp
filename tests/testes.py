import extract_examples
import testes_sinteticos

def generate_dataset():
    sintetic_dataset = testes_sinteticos.gerar_dataset_sintetico()
    repo_dataset = extract_examples.gerar_dataset()
    all_dataset = sintetic_dataset + repo_dataset
    return all_dataset, repo_dataset, sintetic_dataset


