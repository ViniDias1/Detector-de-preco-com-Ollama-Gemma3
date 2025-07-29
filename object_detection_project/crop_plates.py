import cv2
import os
import glob

def crop_plates_from_annotations(base_dataset_dir, output_cropped_dir):
    """
    Recorta as placas das imagens usando as anotações YOLO,
    assumindo que imagens e labels (.txt) estão na mesma subpasta.

    Args:
        base_dataset_dir (str): Caminho para o diretório base que contém as pastas 'train', 'valid', 'test'.
        output_cropped_dir (str): Caminho para o diretório onde as imagens recortadas serão salvas.
    """
    os.makedirs(output_cropped_dir, exist_ok=True)

    subsets = ['train', 'valid', 'test']

    for subset in subsets:
        current_subset_path = os.path.join(base_dataset_dir, subset)

        if not os.path.exists(current_subset_path):
            print(f"Aviso: Pasta de subset '{current_subset_path}' não encontrada. Pulando.")
            continue

        # Lista todos os arquivos de imagem dentro da subpasta atual
        image_files = glob.glob(os.path.join(current_subset_path, '*.jpg')) + \
                      glob.glob(os.path.join(current_subset_path, '*.jpeg')) + \
                      glob.glob(os.path.join(current_subset_path, '*.png'))

        print(f"\nProcessando {len(image_files)} imagens em '{subset}'...")

        for img_file in image_files:
            img_name_without_ext = os.path.splitext(os.path.basename(img_file))[0]
            label_file = os.path.join(current_subset_path, img_name_without_ext + '.txt')

            if not os.path.exists(label_file):
                print(f"Aviso: Arquivo de anotação '{label_file}' não encontrado para {img_file}. Pulando.")
                continue

            # Carregar imagem
            img = cv2.imread(img_file)
            if img is None:
                print(f"Erro: Não foi possível carregar a imagem {img_file}. Pulando.")
                continue

            img_height, img_width = img.shape[:2]
            with open(label_file, 'r') as f:
                annotations = f.readlines()

            for i, line in enumerate(annotations):
                parts = list(map(float, line.strip().split(' ')))
                x_center, y_center, width, height = parts[1:]

                x1 = int((x_center - width / 2) * img_width)
                y1 = int((y_center - height / 2) * img_height)
                x2 = int((x_center + width / 2) * img_width)
                y2 = int((y_center + height / 2) * img_height)

                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(img_width, x2)
                y2 = min(img_height, y2)

                cropped_plate = img[y1:y2, x1:x2]

                if cropped_plate.shape[0] > 0 and cropped_plate.shape[1] > 0:

                    output_filename = os.path.join(output_cropped_dir, f"{subset}_{img_name_without_ext}_cropped_{i}.jpg")
                    cv2.imwrite(output_filename, cropped_plate)
                    print(f"Salvo: {output_filename}")
                else:
                    print(f"Aviso: Recorte vazio para {img_file}, anotação {i+1}. Verifique as coordenadas.")


DATASET_BASE_DIR = 'my_raw_annotated_dataset'


OUTPUT_CROPPED_DIR = 'cropped_plates'

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_full_path = os.path.join(current_dir, DATASET_BASE_DIR)
    output_cropped_full_path = os.path.join(current_dir, OUTPUT_CROPPED_DIR)

    print(f"Processando dataset de: {dataset_full_path}")
    print(f"Imagens recortadas serão salvas em: {output_cropped_full_path}")

    crop_plates_from_annotations(dataset_full_path, output_cropped_full_path)
    print("\nProcesso de recorte concluído!")