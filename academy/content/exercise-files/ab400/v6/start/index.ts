import { IInputs, IOutputs } from "./generated/ManifestTypes";

// STARTER - fill the TODOs. It compiles as is but draws nothing.
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
    const clicked = Number(button.dataset.value);
    // TODO 3: store clicked in this.value, call this.render(), then call this.notifyOutputChanged()
    console.log("Clicked star " + clicked);
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
    // TODO 1: read context.parameters.rating.raw into this.value
    //         read context.parameters.maxStars.raw into this.maxStars (use 5 when empty)
    //         read context.mode.isControlDisabled into this.disabled
    if (this.buttons.length !== this.maxStars) {
      this.buildButtons();
    }
    this.render();
  }

  public getOutputs(): IOutputs {
    // TODO 4: return the rating so the platform writes it to the column
    return {};
  }

  public destroy(): void {
    // TODO 5: remove the click listener from every button
  }

  private buildButtons(): void {
    this.wrapper.innerHTML = "";
    this.buttons = [];
    for (let i = 1; i <= this.maxStars; i++) {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.value = String(i);
      button.setAttribute("role", "radio");
      button.setAttribute("aria-label", i + " of " + this.maxStars + " stars");
      // TODO 2: add this.onStarClick as the "click" listener
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
