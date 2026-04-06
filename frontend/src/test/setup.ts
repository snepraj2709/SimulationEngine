import "@testing-library/jest-dom";

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

class LocalStorageMock {
  private store = new Map<string, string>();

  getItem(key: string) {
    return this.store.get(key) ?? null;
  }

  setItem(key: string, value: string) {
    this.store.set(key, value);
  }

  removeItem(key: string) {
    this.store.delete(key);
  }

  clear() {
    this.store.clear();
  }
}

globalThis.ResizeObserver = ResizeObserverMock as typeof ResizeObserver;
Object.defineProperty(globalThis, "localStorage", {
  value: new LocalStorageMock(),
  configurable: true,
});
