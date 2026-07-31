const ALL_COMMANDS = [
  'Make all headings bold','Make all headings underlined',
  'Make all headings bold and underlined with black color',
  'Set font to Times New Roman 12pt',
  'Set font to Calibri 11pt for body text',
  'Make all text justified','Make all text left aligned',
  'Make all text center aligned',
  'Set line spacing to 1.5','Set line spacing to double',
  'Set margins to 1 inch all sides',
  'Set left margin to 1.5 inches',
  'Highlight all headings in yellow',
  'Highlight all headings in green',
  'Remove all highlights',
  'Make all text uppercase','Make all text lowercase',
  'Add page numbers at bottom right',
  'Add page numbers in format X of Y',
  'Add header with text My Document',
  'Add footer with page numbers',
  'Remove header','Remove footer',
  'Add table of contents',
  'Add clickable table of contents',
  'Apply SPPU format','Apply IEEE format',
  'Apply APA format','Apply MLA format',
  'Apply resume format','Apply Chicago format',
  'Apply thesis format',
  'Add watermark that says DRAFT',
  'Add watermark that says CONFIDENTIAL',
  'Remove watermark',
  'Add cover page with title My Report',
  'Insert a table with 3 rows and 3 columns',
  'Insert a table with headers Name Age City',
  'Color the table header green',
  'Set table borders to black',
  'Add a row to the first table',
  'Add bullet list with items',
  'Add numbered list','Add checklist',
  'Insert a shadow box with text Important Note',
  'Insert a warning box','Insert a tip box',
  'Insert a note box','Insert a caution box',
  'Insert a thick divider','Insert a wave divider',
  'Insert a badge with text NEW',
  'Replace all Company with Organization',
  'Enable track changes','Accept all changes',
  'Add section break','Set two column layout',
  'Make all chapter headings start on new page',
  'Apply heading numbering in 1.1.1 style',
  'Clean empty paragraphs','Normalize spacing',
  'Set password protection',
  'Count words','Count paragraphs',
  'Add citation in APA style',
  'Add bibliography',
  'Set formal style','Set professional style',
  'Set elegant style','Set minimalist style',
  'Add page border','Remove page border',
  'Add footnote','Add endnote',
  'Add hyperlink','Add horizontal line before headings',
  'Insert math equation',
  'Add drop cap to first paragraph',
  'Set line spacing to 1.5',
  'Add line numbers','Remove line numbers',
  'Link all headings',
  'Search and highlight Introduction in yellow',
  'Add shadow effect to headings',
  'Apply small caps to body text',
]

export const useCommandSuggestions = (input) => {
  if (!input || input.trim().length < 2) return []
  const query   = input.toLowerCase().trim()
  const matches = ALL_COMMANDS.filter(cmd =>
    cmd.toLowerCase().includes(query)
  )
  matches.sort((a, b) => {
    const aS = a.toLowerCase().startsWith(query)
    const bS = b.toLowerCase().startsWith(query)
    if (aS && !bS) return -1
    if (!aS && bS) return 1
    return 0
  })
  return matches.slice(0, 6)
}