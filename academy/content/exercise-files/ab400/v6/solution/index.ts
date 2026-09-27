import { IInputs, IOutputs } from "./generated/ManifestTypes";

// SOLUTION - Chd.StarRating field component
export class StarRating implements ComponentFramework.StandardControl<IInputs, IOutputs> {
  private value: number | null = null;
  private maxStars = 5;
  private disabled = false;
  private wrapper!: HTMLDivElement;
  private notifyOutputChanged!: () => void;
  private buttons: HTMLButtonElement[] = [];

  // Arrow function so "this" is the control and the same reference can be removed later.
  private onStarClick = (event: MouseEvent): void => {
    if (this.disabled) {
      return;
    }
    const button = event.currentTarget as HTMLButtonElement;
    this.value = Number(button.dataset.value);
    this.render();
    this.notifyOutputChanged();
  };

  public init(
    context: ComponentFramework.Context<IInputs>,
    notifyOutputChanged: () => void,
    state: ComponentFramework.Dictionary,
    container: HTMLDivElement
  ): void {
    this.notifyOutputChanged = notifyOutputChanged;
    this.wrapper = document.createElement("div");
    this.wrapper.className = "chd-star-rating";
    this.wrapper.setAttribute("role", "radiogroup");
    container.appendChild(this.wrapper);
  }

  public updateView(context: ComponentFramework.Context<IInputs>): void {
    this.value = context.parameters.rating.raw;
    const max = context.parameters.maxStars.raw;
    this.maxStars = max !== null && max > 0 ? max : 5;
    this.disabled = context.mode.isControlDisabled;

    if (this.buttons.length !== this.maxStars) {
      this.buildButtons();
    }
    this.render();
  }

  public getOutputs(): IOutputs {
    return { rating: this.value ?? undefined };
  }

  public destroy(): void {
    this.buttons.forEach((button) => button.removeEventListener("click", this.onStarClick));
    this.buttons = [];
  }

  private buildButtons(): void {
    this.buttons.forEach((button) => button.removeEventListener("click", this.onStarClick));
    this.wrapper.innerHTML = "";
    this.buttons = [];
    for (let i = 1; i <= this.maxStars; i++) {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.value = String(i);
      button.setAttribute("role", "radio");
      button.setAttribute("aria-label", i + " of " + this.maxStars + " stars");
      button.addEventListener("click", this.onStarClick);
      this.wrapper.appendChild(button);
      this.buttons.push(button);
    }
  }

  private render(): void {
    this.buttons.forEach((button, index) => {
      const filled = this.value !== null && index < this.value;
      button.textContent = filled ? "★" : "☆";
      button.className = filled ? "chd-star chd-star--on" : "chd-star";
      button.disabled = this.disabled;
      button.setAttribute("aria-checked", String(this.value === index + 1));
    });
  }
}
