// @ts-check

const genUID = () => {
    const chars = "abcde1234567890"; // 3 bits

    /** @type {string[]} */
    let result = [];
    for (let i = 0; i < 20; i++) { // 60 bits total
        result.push(chars[Math.floor(Math.random() * 16)]);
    }

    return result.join("");
}

/**
 * @param {string} [tagName]
 * @param {{ [key: string]: string | ((self: HTMLElement, ...args: any[]) => void) }} [props]
 * @param {HTMLElement[] | HTMLElement | string | undefined} [children]
 */
const createElement = (tagName, props, children) => {
    let element = document.createElement(tagName);
    for (let prop of Object.keys(props)) {
        let value = props[prop];
        if (typeof value === "string") {
            element.setAttribute(prop, value);
        } else {
            let uid = genUID();
            /** @type {any} */
            let anyWindow = window;
            if (anyWindow.fns === undefined) {
                anyWindow.fns = {};
            }
            anyWindow.fns[uid] = value;
            element.setAttribute(prop, `fns["${uid}"](this, ...arguments)`);
        }
    }

    if (Array.isArray(children)) {
        for (let child of children) {
            element.appendChild(child);
        }
    } else if (typeof children === "string") {
        element.appendChild(document.createTextNode(children));
    } else if (children !== undefined) {
        element.appendChild(children);
    }

    return element;
}

/** @param {string} [name] */
const icon = (name) => createElement("i", { class: "material-icons" }, name);

/** @param {Element | HTMLElement} [element] */
const clearChildren = (element) =>
    [...element.children].map((child) => child.remove());

/** @param {number} [time] */
const formatTime = (time) => {
    /**
     * @param {number} [num]
     * @param {number} [to]
     */
    let padNum = (num, to) => {
        let numStr = num.toString();
        return ("0".repeat(Math.max(0, to - numStr.length))) + numStr;
    }

    let seconds = Math.floor(time) % 60;
    let minutes = Math.floor(time / 60) % 60;
    let hours = Math.floor(time / (60 * 60));

    if (hours > 0) {
        return `${padNum(hours, 2)}:${padNum(minutes, 2)}:${padNum(seconds, 2)}`
    } else {
        return `${padNum(minutes, 2)}:${padNum(seconds, 2)}`
    }

}

export class FrameLoader {
    /** @type {Map<number, string>} */
    frameMap = new Map();

    /** @type  {number} */
    size;

    /** @type {{ frame: number, signal?: AbortSignal, callback?: (data: string) => void }[]} */
    processingQueue = [];

    /** @private @type {number}  */
    nextToProcess = 1;

    /** @private @type {boolean} */
    amLoading = false;


    /**
     * @param {number} [size] - Total number of frames
     */
    constructor(size) {
        this.size = size;
    }

    /**
     * @private
     */
    async loadNextImage() {
        if (this.amLoading) return;
        this.amLoading = true;

        /** @type {number} */
        let frame;
        /** @type {((image: string) => void) | undefined} */
        let callback;
        /** @type {AbortSignal | undefined} */
        let signal;

        if (this.processingQueue.length > 0) {
            let job = this.processingQueue.shift();
            frame = job.frame;
            callback = job.callback;
            signal = job.signal;
        } else {
            frame = this.nextToProcess;
            if (frame >= this.size) {
                this.amLoading = false;
                return;
            }
            this.nextToProcess++;
        }

        let result = await fetch(`/${frame}.svg`, { signal });

        let svgContent = await result.text();
        this.frameMap.set(frame, svgContent);

        callback?.(svgContent);

        this.amLoading = false;
        this.loadNextImage();
    }

    /**
     * @param {number} [index] - Frame index to load
     * @returns {{ cancel: () => void, data: Promise<string> }}
     */
    getImage(index) {
        if (index < 0 || index >= this.size) {
            throw new Error("Frame out of range");
        }

        if (this.frameMap.has(index)) {
            return { cancel: () => undefined, data: Promise.resolve(this.frameMap.get(index)) };
        }

        let abortController = new AbortController();

        /** @type {Promise<string>} */
        let dataPromise = new Promise(async (resolve) => {
            this.processingQueue.push({ frame: index, callback: resolve })
            this.loadNextImage();
        });

        return { cancel: abortController.abort.bind(abortController), data: dataPromise };
    }
}

export class VideoManager {
    /** @type {Element} */
    targetElement;

    /** @type {number} */
    size;

    /** @type {number} */
    frameRate;

    /** @type { FrameLoader } */
    frameLoader;

    /** @type {number} */
    index = -1;

    /** @type {(() => void) | undefined} */
    cancelLoad;

    /** @type {{ kind: "paused"} | { kind: "playing", stop: () => void }} */
    playState = { kind: "paused" }

    /**
     * @param {string} [target] - A css selector for where to render
     * @param {number} [size]
     * @param {number} [frameRate]
     */
    constructor(target, size, frameRate) {
        this.targetElement = document.querySelector(target);
        this.size = size;
        this.frameRate = frameRate;

        if (this.targetElement === undefined) {
            throw new Error(`Unable to find target: ${target}`);
        }

        // Who needs JSX
        const frameDOM = createElement("div", { class: "video-player" }, [
            createElement("div", { class: "video-frame" }),
            createElement("div", { class: "video-nav" }, [
                createElement("div", { class: "time current-time" }, "0:00"),
                createElement(
                    "input",
                    {
                        class: "seeker",
                        type: "range",
                        min: "0",
                        max: (size - 1).toString(),
                        oninput: (target) => {
                            let asInput = /** @type {HTMLInputElement} */ /** @type {any} */ (target);
                            let value = asInput.value;
                            let newIndex = parseInt(value);
                            this.render(newIndex);
                        }
                    }
                ),
                createElement("div", { class: "time total-time" }, "0:00"),
            ]),
            createElement("div", { class: "video-controls" }, [
                createElement(
                    "div",
                    { class: "button prev", onclick: () => this.render(this.index - 1) },
                    icon("skip_previous")
                ),
                createElement(
                    "div",
                    { class: "button play-pause", onclick: () => this.playPause() },
                    icon("play_arrow")
                ),
                createElement(
                    "div",
                    { class: "button next", onclick: () => this.render(this.index + 1) },
                    icon("skip_next")
                ),
            ])
        ]);

        clearChildren(this.targetElement);
        this.targetElement.appendChild(frameDOM);

        this.frameLoader = new FrameLoader(size);

        this.render(0);
    }

    /**
     * @param {number} [index]
     */
    async render(index) {
        if (index === this.index) {
            return;
        }

        if (index >= this.size) {
            this.pause();
            return;
        }

        if (this.cancelLoad !== undefined) {
            this.cancelLoad();
            this.cancelLoad = undefined;
        }

        this.index = index;

        let destElement = this.targetElement.querySelector(".video-frame");
        let { cancel, data } = this.frameLoader.getImage(index);
        this.cancelLoad = cancel;
        destElement.innerHTML = await data;
        this.cancelLoad = undefined;

        let currentTimeTarget = /** @type {HTMLDivElement} */ (this.targetElement.querySelector(".current-time"));
        currentTimeTarget.innerText = formatTime(this.index / this.frameRate);

        let totalTimeTarget = /** @type {HTMLDivElement} */ (this.targetElement.querySelector(".total-time"));
        totalTimeTarget.innerText = formatTime(this.size / this.frameRate);

        /** @type { HTMLInputElement } */
        let seeker = this.targetElement.querySelector(".seeker");
        seeker.value = index.toString();
    }

    play() {
        if (this.playState.kind === "playing") {
            return;
        }

        let interval = setInterval(async () => {
            await this.render(this.index + 1);
        }, 1000 / this.frameRate);

        let pauseButton = this.targetElement.querySelector(".play-pause");
        clearChildren(pauseButton);
        pauseButton.appendChild(icon("pause"));

        this.playState = { kind: "playing", stop: () => clearInterval(interval) };
    }

    pause() {
        if (this.playState.kind === "paused") {
            return;
        }

        this.playState.stop();

        let pauseButton = this.targetElement.querySelector(".play-pause");
        clearChildren(pauseButton);
        pauseButton.appendChild(icon("play_arrow"));

        this.playState = { kind: "paused" };
    }

    playPause() {
        if (this.playState.kind === "playing") {
            this.pause();
        } else {
            this.play();
        }
    }
}