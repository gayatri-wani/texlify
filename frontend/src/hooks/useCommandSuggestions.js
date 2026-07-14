const ALL_COMMANDS = [
  // Formatting
  'Make all headings bold',
  'Make all headings bold and underlined',
  'Make all headings italic',
  'Set font to Times New Roman 12pt',
  'Set font to Calibri 11pt',
  'Set font to Arial 12pt',
  'Set heading font size to 14pt',
  'Set body text font size to 12pt',
  'Make all text justified',
  'Make all text left aligned',
  'Make all text center aligned',
  'Set line spacing to 1.5',
  'Set line spacing to double',
  'Set line spacing to single',
  'Set margins to 1 inch all sides',
  'Set left margin to 1.5 inches',
  'Remove all formatting',
  'Make headings green',
  'Make headings blue',
  'Make headings red',
  'Set text color to black',
  'Highlight all headings in yellow',
  'Highlight all headings in green',
  'Highlight all headings in cyan',
  'Remove all highlights',
  'Make all text uppercase',
  'Make all text lowercase',
  'Make all text title case',
  'Add underline to all headings',
  'Add strikethrough to selected text',
  'Set character spacing to 1.5',
  'Add drop cap to first paragraph',

  // Page
  'Add page break',
  'Add blank page',
  'Set page size to A4',
  'Set page size to Letter',
  'Set page orientation to landscape',
  'Set page orientation to portrait',
  'Set page background color to light blue',
  'Add line numbers',
  'Remove line numbers',
  'Set page number start at 1',

  // Headers and Footers
  'Add header with document title',
  'Add footer with page numbers',
  'Add page numbers at bottom right',
  'Add page numbers at bottom center',
  'Add page numbers in format X of Y',
  'Remove header',
  'Remove footer',
  'Add different first page header',
  'Insert date field',
  'Insert page count field',

  // Lists
  'Convert to bullet list',
  'Add numbered list',
  'Add multilevel list',
  'Add checklist',
  'Convert to checklist',

  // Tables
  'Insert a table with 3 rows and 3 columns',
  'Insert a table with 5 rows and 4 columns',
  'Add a row to the first table',
  'Color the table header green',
  'Set table borders to black',
  'Sort the table by first column',
  'Merge first two cells of first row',

  // References
  'Add table of contents',
  'Add table of figures',
  'Add index',
  'Add footnote',
  'Add endnote',
  'Add bookmark',
  'Add cross reference',
  'Add hyperlink',

  // Document elements
  'Add watermark that says DRAFT',
  'Add watermark that says CONFIDENTIAL',
  'Remove watermark',
  'Add cover page',
  'Insert text box',
  'Insert math equation',
  'Format code blocks',
  'Add horizontal line before headings',
  'Add page border',
  'Remove page border',
  'Add comment',
  'Remove all comments',

  // Formats
  'Apply SPPU format',
  'Apply IEEE format',
  'Apply APA format',
  'Apply MLA format',
  'Apply resume format',
  'Apply Chicago format',
  'Apply thesis format',
  'Apply formal style',
  'Apply professional style',
  'Apply elegant style',

  // Sections
  'Add section break',
  'Set two column layout',
  'Set single column layout',
  'Make all chapter headings start on new page',

  // Find and replace
  'Replace all "Company" with "Organization"',
  'Replace all double spaces with single space',
  'Delete all occurrences of "TODO"',
  'Find and replace',

  // Track changes
  'Enable track changes',
  'Accept all changes',
  'Reject all changes',
  'Disable track changes',

  // Document info
  'Count words',
  'Count paragraphs',
  'Set document title',
  'Set document author',

  // Maintenance
  'Clean empty paragraphs',
  'Normalize spacing',
  'Clear document',
  'Add heading numbering in 1.1.1 style',
  'Remove heading numbers',

  // Protection
  'Set password protection',
  'Remove password protection',
  'Convert to PDF',

  // SmartArt
  'Insert process SmartArt',
  'Insert hierarchy SmartArt',
  'Insert list SmartArt',

  // Citations
  'Add citation in APA style',
  'Add bibliography',
  'Add mail merge field',
]

export const useCommandSuggestions = (input) => {
  if (!input || input.trim().length < 2) return []

  const query = input.toLowerCase().trim()

  const matches = ALL_COMMANDS.filter(cmd =>
    cmd.toLowerCase().includes(query)
  )

  // Sort: commands that start with the query first
  matches.sort((a, b) => {
    const aStarts = a.toLowerCase().startsWith(query)
    const bStarts = b.toLowerCase().startsWith(query)
    if (aStarts && !bStarts) return -1
    if (!aStarts && bStarts) return 1
    return 0
  })

  return matches.slice(0, 6)
}