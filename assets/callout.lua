--- callout.lua — Convert GFM alert syntax to cosaicallout LaTeX environments.
--
-- Handles two AST shapes produced by Pandoc:
--   1. Div elements (Pandoc 3.9 with +alerts extension):
--        Div ("", ["note"], []) [Div ("", ["title"], []) [...], ...]
--   2. BlockQuotes (older Pandoc or without +alerts):
--        BlockQuote [Para [Str "[!NOTE]", ...], ...]
--
-- Supported types: note, tip, important, warning, caution

local valid_types = {
  note = true,
  tip = true,
  important = true,
  warning = true,
  caution = true,
}

--- Handle Div elements produced by Pandoc 3.9 alerts extension.
-- The extension parses `> [!NOTE]` into:
--   Div ("", ["note"], []) [Div ("", ["title"], []) [Para [Str "Note"]], ...]
function Div(el)
  -- Check if any class matches a valid alert type
  for _, cls in ipairs(el.classes) do
    if valid_types[cls] then
      -- Remove the title div (first child with class "title")
      local content = pandoc.List()
      for _, block in ipairs(el.content) do
        if block.t ~= "Div" or not block.classes:includes("title") then
          content:insert(block)
        end
      end
      -- Wrap in LaTeX environment
      table.insert(content, 1,
        pandoc.RawBlock("latex", "\\begin{cosaicallout}{" .. cls .. "}"))
      content:insert(
        pandoc.RawBlock("latex", "\\end{cosaicallout}"))
      return content
    end
  end
end

--- Handle BlockQuotes with [!TYPE] markers (fallback for older Pandoc).
local alert_pattern = "^%[!(%u+)%]"

function BlockQuote(el)
  if #el.content == 0 then return nil end
  local first = el.content[1]
  if first.t ~= "Para" or #first.content == 0 then return nil end

  local first_inline = first.content[1]
  if first_inline.t ~= "Str" then return nil end

  local alert_type = first_inline.text:match(alert_pattern)
  if not alert_type or not valid_types[alert_type:lower()] then return nil end

  -- Build content blocks, skipping the [!TYPE] marker and any
  -- immediately following SoftBreak from the first paragraph.
  local remaining_inlines = pandoc.List()
  local skip_break = true
  for i = 2, #first.content do
    local inl = first.content[i]
    if skip_break and (inl.t == "SoftBreak" or inl.t == "LineBreak" or inl.t == "Space") then
      skip_break = false
    else
      skip_break = false
      remaining_inlines:insert(inl)
    end
  end

  local content = pandoc.List()
  content:insert(pandoc.RawBlock("latex",
    "\\begin{cosaicallout}{" .. alert_type:lower() .. "}"))

  if #remaining_inlines > 0 then
    content:insert(pandoc.Para(remaining_inlines))
  end

  for i = 2, #el.content do
    content:insert(el.content[i])
  end

  content:insert(pandoc.RawBlock("latex", "\\end{cosaicallout}"))
  return content
end
