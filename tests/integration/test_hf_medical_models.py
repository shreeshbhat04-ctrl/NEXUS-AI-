from pprint import pprint

from nexus_ai.services.huggingface_medical import HuggingFaceMedicalService


def main() -> None:
    service = HuggingFaceMedicalService()
    print("CONFIGURED", service.is_configured())
    if not service.is_configured():
        print("Set MEDICAL_MODEL_BACKEND=huggingface, provide HUGGINGFACE_HUB_TOKEN, and install the optional HF dependencies.")
        return

    medgemma = service.medgemma_generate(prompt="What animal is on the candy?", image_path="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/p-blog/candy.JPG", max_new_tokens=40)
    print("MEDGEMMA")
    pprint(medgemma)

    medsiglip = service.medsiglip_classify(
        image_path="https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/hub/parrots.png",
        candidate_labels=["animals", "humans", "landscape"],
    )
    print("MEDSIGLIP")
    pprint(medsiglip)


if __name__ == "__main__":
    main()
