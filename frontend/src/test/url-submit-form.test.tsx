import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { URLSubmitForm } from "@/components/forms/URLSubmitForm";

describe("URLSubmitForm", () => {
  it("starts empty and uses Netflix as placeholder text only", () => {
    render(<URLSubmitForm onSubmit={vi.fn()} />);

    const input = screen.getByPlaceholderText("https://www.netflix.com/") as HTMLInputElement;

    expect(input.value).toBe("");
  });

  it("validates URL input before submit", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<URLSubmitForm onSubmit={onSubmit} />);

    const input = screen.getByPlaceholderText("https://www.netflix.com/");
    await user.clear(input);
    await user.type(input, "not-a-url");
    await user.click(screen.getByRole("button", { name: /analyze url/i }));

    expect(await screen.findByText(/enter a valid company or product url/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("accepts a bare domain and normalizes it to http before submit", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<URLSubmitForm onSubmit={onSubmit} />);

    const input = screen.getByPlaceholderText("https://www.netflix.com/");
    await user.clear(input);
    await user.type(input, "incommon.ai");
    await user.click(screen.getByRole("button", { name: /analyze url/i }));

    expect(onSubmit).toHaveBeenCalledWith({ url: "http://incommon.ai/" }, expect.anything());
  });
});
