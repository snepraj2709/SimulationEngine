import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { URLSubmitForm } from "@/components/forms/URLSubmitForm";

describe("URLSubmitForm", () => {
  it("validates URL input before submit", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<URLSubmitForm onSubmit={onSubmit} />);

    const input = screen.getByPlaceholderText("https://www.example.com/");
    await user.clear(input);
    await user.type(input, "not-a-url");
    await user.click(screen.getByRole("button", { name: /analyze url/i }));

    expect(await screen.findByText(/enter a valid company or product url/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
