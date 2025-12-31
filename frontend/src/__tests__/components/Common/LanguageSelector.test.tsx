import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LanguageSelector } from '../../../components/Common/LanguageSelector';

// Create mock changeLanguage function
const mockChangeLanguage = vi.fn();

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: vi.fn(() => ({
    i18n: {
      changeLanguage: mockChangeLanguage,
      language: 'en',
    },
    t: (key: string) => key,
  })),
}));

describe('LanguageSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render button with current language', () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button', {
        name: /Select language\. Current language: English/i,
      });
      expect(button).toBeInTheDocument();
    });

    it('should show current language flag emoji', () => {
      render(<LanguageSelector />);
      const flagEmoji = screen.getByText('🇬🇧');
      expect(flagEmoji).toBeInTheDocument();
    });

    it('should show current language name on larger screens', () => {
      render(<LanguageSelector />);
      const languageName = screen.getByText('English');
      expect(languageName).toBeInTheDocument();
    });

    it('should render with dropdown initially closed', () => {
      render(<LanguageSelector />);
      const menu = screen.queryByRole('menu');
      expect(menu).not.toBeInTheDocument();
    });

    it('should have aria-label with current language info', () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute(
        'aria-label',
        expect.stringContaining('English')
      );
    });

    it('should have aria-expanded set to false initially', () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-expanded', 'false');
    });

    it('should have aria-haspopup menu attribute', () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-haspopup', 'menu');
    });
  });

  describe('Dropdown Interaction', () => {
    it('should open dropdown on button click', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      await user.click(button);

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });
    });

    it('should close dropdown on button click again (toggle)', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      // Open dropdown
      await user.click(button);
      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Close dropdown
      await user.click(button);
      await waitFor(() => {
        expect(screen.queryByRole('menu')).not.toBeInTheDocument();
      });
    });

    it('should close dropdown when clicking outside', async () => {
      const { container } = render(
        <div>
          <LanguageSelector />
          <div data-testid="outside-element">Outside</div>
        </div>
      );

      const button = screen.getByRole('button');
      const user = userEvent.setup();

      // Open dropdown
      await user.click(button);
      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Click outside
      const outsideElement = screen.getByTestId('outside-element');
      await user.click(outsideElement);

      await waitFor(() => {
        expect(screen.queryByRole('menu')).not.toBeInTheDocument();
      });
    });

    it('should show all 3 languages in dropdown', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      await user.click(button);

      await waitFor(() => {
        const menuItems = screen.getAllByRole('menuitem');
        expect(menuItems).toHaveLength(3);
        // Check each menu item has the language names
        expect(menuItems[0]).toHaveTextContent('English');
        expect(menuItems[1]).toHaveTextContent('Deutsch');
        expect(menuItems[2]).toHaveTextContent('Polski');
      });
    });

    it('should have aria-expanded set to true when open', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      await user.click(button);

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-expanded', 'true');
      });
    });
  });

  describe('Language Change', () => {
    it('should call i18n.changeLanguage when language is selected', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      await user.click(button);

      const deutschOption = screen.getByText('Deutsch');
      await user.click(deutschOption);

      expect(mockChangeLanguage).toHaveBeenCalledWith('de');
    });

    it('should close dropdown after language selection', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      await user.click(button);
      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      const deutschOption = screen.getByText('Deutsch');
      await user.click(deutschOption);

      await waitFor(() => {
        expect(screen.queryByRole('menu')).not.toBeInTheDocument();
      });
    });

    it('should show checkmark on current language', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      await user.click(button);

      await waitFor(() => {
        const englishButton = screen.getByRole('menuitem', {
          name: /English/i,
        });
        // The checkmark is rendered as an SVG within the button
        const checkmarkSvg = englishButton.querySelector('svg');
        expect(checkmarkSvg).toBeInTheDocument();
      });
    });

    it('should highlight current language in dropdown', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      await user.click(button);

      await waitFor(() => {
        const englishMenuItem = screen.getByRole('menuitem', {
          name: /English/i,
        });
        // Current language should have aria-current attribute
        expect(englishMenuItem).toHaveAttribute('aria-current', 'true');
      });
    });

    it('should only show checkmark on current language, not others', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      await user.click(button);

      await waitFor(() => {
        const menuItems = screen.getAllByRole('menuitem');
        const englishItem = menuItems[0];
        const deutschItem = menuItems[1];

        const englishCheckmark = englishItem.querySelector('svg');
        const deutschCheckmark = deutschItem.querySelector('svg');

        expect(englishCheckmark).toBeInTheDocument();
        expect(deutschCheckmark).not.toBeInTheDocument();
      });
    });
  });

  describe('Keyboard Navigation', () => {
    it('should open dropdown with ArrowDown on button', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      button.focus();
      await user.keyboard('{ArrowDown}');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });
    });

    it('should close dropdown with Escape key', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      // Open dropdown
      await user.click(button);
      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Close with Escape
      await user.keyboard('{Escape}');

      await waitFor(() => {
        expect(screen.queryByRole('menu')).not.toBeInTheDocument();
      });
    });

    it('should return focus to button after Escape key', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      button.focus();
      await user.keyboard('{ArrowDown}');
      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      await user.keyboard('{Escape}');

      await waitFor(() => {
        expect(button).toHaveFocus();
      });
    });

    it('should navigate through menu items with ArrowDown', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      // Open dropdown
      button.focus();
      await user.keyboard('{ArrowDown}');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Navigate down - should focus first menu item
      await user.keyboard('{ArrowDown}');

      const menuItems = screen.getAllByRole('menuitem');
      expect(menuItems[0]).toHaveFocus();

      // Navigate down - should focus second menu item
      await user.keyboard('{ArrowDown}');
      expect(menuItems[1]).toHaveFocus();
    });

    it('should navigate through menu items with ArrowUp', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      // Open dropdown
      button.focus();
      await user.keyboard('{ArrowDown}');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Navigate to first item with ArrowDown
      await user.keyboard('{ArrowDown}');

      const menuItems = screen.getAllByRole('menuitem');
      expect(menuItems[0]).toHaveFocus();

      // Navigate up from first should wrap to last
      await user.keyboard('{ArrowUp}');
      expect(menuItems[2]).toHaveFocus();

      // Navigate up again - should focus second menu item
      await user.keyboard('{ArrowUp}');
      expect(menuItems[1]).toHaveFocus();
    });

    it('should wrap navigation from last to first with ArrowDown', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      // Open dropdown
      button.focus();
      await user.keyboard('{ArrowDown}');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Move to last item
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{ArrowDown}');

      const menuItems = screen.getAllByRole('menuitem');
      expect(menuItems[2]).toHaveFocus();

      // Press ArrowDown again - should wrap to first
      await user.keyboard('{ArrowDown}');
      expect(menuItems[0]).toHaveFocus();
    });

    it('should wrap navigation from first to last with ArrowUp', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      // Open dropdown and navigate to first item
      button.focus();
      await user.keyboard('{ArrowDown}');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      await user.keyboard('{ArrowDown}');

      const menuItems = screen.getAllByRole('menuitem');
      expect(menuItems[0]).toHaveFocus();

      // Press ArrowUp again - should wrap to last
      await user.keyboard('{ArrowUp}');
      expect(menuItems[2]).toHaveFocus();
    });

    it('should focus first item with Home key', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      // Open dropdown
      button.focus();
      await user.keyboard('{ArrowDown}');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Navigate to last item
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{ArrowDown}');

      const menuItems = screen.getAllByRole('menuitem');
      expect(menuItems[2]).toHaveFocus();

      // Move to first with Home
      await user.keyboard('{Home}');

      expect(menuItems[0]).toHaveFocus();
    });

    it('should focus last item with End key', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      // Open dropdown
      button.focus();
      await user.keyboard('{ArrowDown}');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Navigate to first item
      await user.keyboard('{ArrowDown}');

      // Move to end with End key
      await user.keyboard('{End}');

      const menuItems = screen.getAllByRole('menuitem');
      expect(menuItems[2]).toHaveFocus();
    });

    it('should allow selecting item with Enter key', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      // Open dropdown
      button.focus();
      await user.keyboard('{ArrowDown}');

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Navigate to second item (Deutsch)
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{ArrowDown}');

      // Press Enter
      await user.keyboard('{Enter}');

      expect(mockChangeLanguage).toHaveBeenCalledWith('de');
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA label on button', () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label');
      expect(button.getAttribute('aria-label')).toMatch(/Select language/i);
    });

    it('should have aria-expanded attribute', () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-expanded');
    });

    it('should update aria-expanded when dropdown opens and closes', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      expect(button).toHaveAttribute('aria-expanded', 'false');

      await user.click(button);

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-expanded', 'true');
      });

      await user.click(button);

      await waitFor(() => {
        expect(button).toHaveAttribute('aria-expanded', 'false');
      });
    });

    it('should have menu role on dropdown', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      await user.click(button);

      await waitFor(() => {
        const menu = screen.getByRole('menu');
        expect(menu).toHaveAttribute('role', 'menu');
      });
    });

    it('should have menuitem role on language options', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      await user.click(button);

      await waitFor(() => {
        const menuItems = screen.getAllByRole('menuitem');
        expect(menuItems.length).toBe(3);
        menuItems.forEach((item) => {
          expect(item).toHaveAttribute('role', 'menuitem');
        });
      });
    });

    it('should return focus to button after language selection', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      // Open dropdown
      await user.click(button);
      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Select language
      const deutschOption = screen.getByText('Deutsch');
      await user.click(deutschOption);

      await waitFor(() => {
        expect(button).toHaveFocus();
      });
    });

    it('should hide flag emoji from screen readers', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      const flags = screen.getAllByText(/🇬🇧|🇩🇪|🇵🇱/);
      flags.forEach((flag) => {
        expect(flag).toHaveAttribute('aria-hidden', 'true');
      });
    });

    it('should have aria-current on selected language item', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      await user.click(button);

      await waitFor(() => {
        const englishItem = screen.getByRole('menuitem', {
          name: /English/i,
        });
        expect(englishItem).toHaveAttribute('aria-current', 'true');
      });
    });

    it('should not have aria-current on non-selected items', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      await user.click(button);

      await waitFor(() => {
        const menuItems = screen.getAllByRole('menuitem');
        expect(menuItems[1]).not.toHaveAttribute('aria-current');
        expect(menuItems[2]).not.toHaveAttribute('aria-current');
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle rapid button clicks', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      // Click to open
      await user.click(button);
      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Click to close
      await user.click(button);
      await waitFor(() => {
        expect(screen.queryByRole('menu')).not.toBeInTheDocument();
      });

      // Click to open again
      await user.click(button);
      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });
    });

    it('should close dropdown when selecting current language', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      await user.click(button);
      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Click on current language (English) - use getAllByRole to avoid duplication issues
      const menuItems = screen.getAllByRole('menuitem');
      await user.click(menuItems[0]);

      await waitFor(() => {
        expect(screen.queryByRole('menu')).not.toBeInTheDocument();
      });
    });

    it('should call changeLanguage even when selecting current language', async () => {
      render(<LanguageSelector />);
      const button = screen.getByRole('button');
      const user = userEvent.setup();

      await user.click(button);

      await waitFor(() => {
        expect(screen.getByRole('menu')).toBeInTheDocument();
      });

      // Get the first menu item (English)
      const menuItems = screen.getAllByRole('menuitem');
      await user.click(menuItems[0]);

      expect(mockChangeLanguage).toHaveBeenCalledWith('en');
    });
  });
});
