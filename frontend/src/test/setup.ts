import '@testing-library/jest-dom/vitest'

class ResizeObserverMock implements ResizeObserver {
  constructor(private readonly callback: ResizeObserverCallback) {}

  disconnect() {}

  observe(target: Element) {
    const contentRect = new DOMRectReadOnly(0, 0, 800, 300)
    this.callback(
      [
        {
          borderBoxSize: [],
          contentBoxSize: [],
          contentRect,
          devicePixelContentBoxSize: [],
          target,
        },
      ],
      this,
    )
  }

  unobserve() {}
}

globalThis.ResizeObserver = ResizeObserverMock
