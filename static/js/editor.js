document.addEventListener('DOMContentLoaded', function () {
  var textarea = document.querySelector('textarea[name="content"]');
  if (!textarea) return;

  var wrapper = document.createElement('div');
  wrapper.className = 'wysiwyg-wrapper';

  var toolbar = document.createElement('div');
  toolbar.className = 'wysiwyg-toolbar';

  var editable = document.createElement('div');
  editable.className = 'wysiwyg-editable';
  editable.contentEditable = 'true';
  editable.innerHTML = textarea.value || '';

  try {
    document.execCommand('defaultParagraphSeparator', false, 'p');
    document.execCommand('styleWithCSS', false, true);
  } catch (e) { /* not supported in all browsers, harmless */ }

  var buttons = [
    { label: '<b>B</b>', title: 'Bold', cmd: 'bold' },
    { label: '<i>I</i>', title: 'Italic', cmd: 'italic' },
    { label: '<u>U</u>', title: 'Underline', cmd: 'underline' },
    { label: 'H2', title: 'Heading 2', cmd: 'formatBlock', arg: 'H2' },
    { label: 'H3', title: 'Heading 3', cmd: 'formatBlock', arg: 'H3' },
    { label: 'P', title: 'Paragraph', cmd: 'formatBlock', arg: 'P' },
    { label: '&bull; List', title: 'Bullet List', cmd: 'insertUnorderedList' },
    { label: '1. List', title: 'Numbered List', cmd: 'insertOrderedList' },
    { label: '&ldquo;Quote', title: 'Blockquote', cmd: 'formatBlock', arg: 'BLOCKQUOTE' },
    { label: 'Link', title: 'Insert Link', cmd: 'link' },
    { label: 'Clear', title: 'Clear Formatting', cmd: 'removeFormat' },
    { label: '&#8630;', title: 'Undo', cmd: 'undo' },
    { label: '&#8631;', title: 'Redo', cmd: 'redo' },
  ];

  buttons.forEach(function (b) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'wysiwyg-btn';
    btn.title = b.title;
    btn.innerHTML = b.label;
    btn.addEventListener('mousedown', function (e) {
      e.preventDefault(); // keep focus/selection in the editable area
      editable.focus();
      if (b.cmd === 'link') {
        var url = window.prompt('Link URL (https://...)');
        if (url) document.execCommand('createLink', false, url);
        return;
      }
      document.execCommand(b.cmd, false, b.arg || null);
      sync();
    });
    toolbar.appendChild(btn);
  });

  var savedRange = null;
  editable.addEventListener('mouseup', saveRange);
  editable.addEventListener('keyup', saveRange);
  function saveRange() {
    var sel = window.getSelection();
    if (sel.rangeCount > 0 && editable.contains(sel.anchorNode)) {
      savedRange = sel.getRangeAt(0);
    }
  }
  function restoreRange() {
    if (!savedRange) return;
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(savedRange);
  }

  var sizeSelect = document.createElement('select');
  sizeSelect.className = 'wysiwyg-size-select';
  sizeSelect.title = 'Text size';
  [
    { label: 'Size', value: '' },
    { label: 'Small', value: '13px' },
    { label: 'Normal', value: '16px' },
    { label: 'Large', value: '20px' },
    { label: 'Extra large', value: '26px' },
  ].forEach(function (opt) {
    var o = document.createElement('option');
    o.value = opt.value;
    o.textContent = opt.label;
    sizeSelect.appendChild(o);
  });
  sizeSelect.addEventListener('mousedown', saveRange);
  sizeSelect.addEventListener('change', function () {
    var size = sizeSelect.value;
    sizeSelect.value = '';
    if (!size) return;
    editable.focus();
    restoreRange();
    document.execCommand('styleWithCSS', false, false);
    document.execCommand('fontSize', false, '7');
    document.execCommand('styleWithCSS', false, true);
    editable.querySelectorAll('font[size="7"]').forEach(function (fontEl) {
      var span = document.createElement('span');
      span.style.fontSize = size;
      while (fontEl.firstChild) span.appendChild(fontEl.firstChild);
      fontEl.replaceWith(span);
    });
    sync();
  });
  toolbar.appendChild(sizeSelect);

  function addColorPicker(title, defaultColor, apply) {
    var wrap = document.createElement('label');
    wrap.className = 'wysiwyg-color-btn';
    wrap.title = title;

    var swatch = document.createElement('span');
    swatch.className = 'wysiwyg-color-swatch';
    swatch.textContent = 'A';
    swatch.style.borderBottomColor = defaultColor;
    wrap.appendChild(swatch);

    var input = document.createElement('input');
    input.type = 'color';
    input.value = defaultColor;
    input.addEventListener('input', function () {
      editable.focus();
      apply(input.value);
      swatch.style.borderBottomColor = input.value;
      sync();
    });
    wrap.appendChild(input);
    toolbar.appendChild(wrap);
  }

  addColorPicker('Text color', '#1a1a1a', function (color) {
    document.execCommand('foreColor', false, color);
  });
  addColorPicker('Highlight / background color', '#fff3b0', function (color) {
    if (!document.execCommand('hiliteColor', false, color)) {
      document.execCommand('backColor', false, color);
    }
  });

  function sync() {
    textarea.value = editable.innerHTML;
  }

  editable.addEventListener('input', sync);
  editable.addEventListener('blur', sync);

  var form = textarea.closest('form');
  if (form) {
    form.addEventListener('submit', sync);
  }

  textarea.style.display = 'none';
  textarea.parentNode.insertBefore(wrapper, textarea);
  wrapper.appendChild(toolbar);
  wrapper.appendChild(editable);
  wrapper.appendChild(textarea);

  sync();
});
