import type { Editor } from "@tiptap/react";
import { api } from "../api";
import { notify } from "../components/Toaster";

const IMAGE_TYPES = ["image/png", "image/jpeg", "image/gif", "image/webp"];

export function imageFiles(list: FileList | File[] | null | undefined) {
  return Array.from(list ?? []).filter((f) => IMAGE_TYPES.includes(f.type));
}

export async function uploadImage(file: File) {
  const form = new FormData();
  form.append("file", file);
  return api<{ id: string; url: string }>("/assets/", { method: "POST", body: form });
}

/** Upload images and insert them at `pos` (or the cursor). */
export async function insertImages(editor: Editor, files: File[], pos?: number) {
  for (const file of files) {
    try {
      const { url } = await uploadImage(file);
      const chain = editor.chain().focus();
      if (pos !== undefined) chain.insertContentAt(pos, { type: "image", attrs: { src: url, alt: file.name } });
      else chain.setImage({ src: url, alt: file.name });
      chain.run();
    } catch (e) {
      notify(`Couldn't upload ${file.name}: ${(e as Error).message}`, "error");
    }
  }
}

/** Open the file chooser and insert the chosen images. */
export function pickImages(editor: Editor) {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = IMAGE_TYPES.join(",");
  input.multiple = true;
  input.onchange = () => void insertImages(editor, imageFiles(input.files));
  input.click();
}
