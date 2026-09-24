--[[
Open a link in a new tab when following it would take the visitor off the page
they are reading: any link to another site, and any link to a document on this
site (the CV PDF, and papers, slides or posters added under assets/files/).

This runs at build time, so the attributes are in the HTML Quarto writes. That
matters: the same behaviour done in the browser depends on JavaScript running,
does not show up in "View Source", and is awkward to verify.

Quarto's own `link-external-newwindow: true` emits nothing in 1.10.18, which is
why this filter exists.

It only sees links in page *content*. The navbar icons, the About-page link
buttons and the footer are emitted by Quarto's templates, so those carry their
own `target`/`rel` in _quarto.yml and index.qmd.
--]]

local SITE_HOST = "lenaliebich.github.io"

local DOCUMENT_EXTENSIONS = {
  pdf = true,
  doc = true, docx = true,
  ppt = true, pptx = true,
  xls = true, xlsx = true,
  csv = true, zip = true,
}

-- "paper.pdf?v=2#page=3" -> "paper.pdf"
local function path_only(href)
  return (href:gsub("[?#].*$", ""))
end

local function is_document(href)
  local extension = path_only(href):match("%.([%a%d]+)$")
  return extension ~= nil and DOCUMENT_EXTENSIONS[extension:lower()] == true
end

local function host_of(href)
  local host = href:match("^%a[%w+.-]*://([^/?#]+)") or href:match("^//([^/?#]+)")
  if host == nil then
    return nil
  end
  -- Drop any credentials and port, then a leading www.
  host = host:gsub("^[^@]*@", ""):gsub(":%d+$", "")
  return (host:lower():gsub("^www%.", ""))
end

local function open_in_new_tab(el, rel)
  el.attributes["target"] = "_blank"
  el.attributes["rel"] = rel
  return el
end

function Link(el)
  local href = el.target
  if href == nil or href == "" then
    return nil
  end

  -- In-page anchor
  if href:sub(1, 1) == "#" then
    return nil
  end

  local scheme = href:match("^(%a[%w+.-]*):")
  local is_protocol_relative = href:sub(1, 2) == "//"

  if scheme ~= nil and not is_protocol_relative then
    local s = scheme:lower()
    -- Leaves mailto:, tel: and anything else alone
    if s ~= "http" and s ~= "https" then
      return nil
    end
  end

  if scheme ~= nil or is_protocol_relative then
    local host = host_of(href)
    if host ~= nil and host ~= SITE_HOST then
      -- Another site: deny the new tab access to window.opener (tabnabbing)
      -- and withhold the referrer.
      return open_in_new_tab(el, "noopener noreferrer")
    end
    -- An absolute link back to our own site
    if is_document(href) then
      return open_in_new_tab(el, "noopener")
    end
    return nil
  end

  -- Relative link, so our own site: pages stay in this tab, documents do not
  if is_document(href) then
    return open_in_new_tab(el, "noopener")
  end

  return nil
end
