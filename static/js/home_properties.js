const DEFAULT_IMG = '/static/images/default_property.png';

document.addEventListener('DOMContentLoaded', () => {
  loadProperties();
});

async function loadProperties() {
  try {
    // Load both the property list and any custom images in parallel
    const [propRes, imgRes] = await Promise.all([
      fetch('/api/properties'),
      fetch('/api/property_images'),
    ]);
    if (!propRes.ok) throw new Error('Failed to fetch properties');

    const properties = await propRes.json();
    const imageMap   = imgRes.ok ? await imgRes.json() : {};

    const container = document.getElementById('propertyShowcase');
    if (!container) return;
    container.innerHTML = '';

    properties.forEach(prop => {
      const card = buildCard(prop, imageMap);
      container.appendChild(card);
    });
  } catch (err) {
    console.error('Failed to load properties:', err);
  }
}

function buildCard(prop, imageMap) {
  const card = document.createElement('div');
  card.className = 'property-card';

  // ── Image ──────────────────────────────────────────────────
  const imgWrap = document.createElement('div');
  imgWrap.className = 'img-wrap';
  imgWrap.style.cssText = 'position:relative; overflow:hidden;';

  const img = document.createElement('img');
  img.src = imageMap[prop.id] || prop.image_url || DEFAULT_IMG;
  img.alt = prop.title || 'Property Image';
  img.style.cssText = 'width:100%; height:220px; object-fit:cover; display:block;';
  imgWrap.appendChild(img);

  // ── Upload button (pencil icon overlay) ────────────────────
  const uploadBtn = document.createElement('label');
  uploadBtn.title  = 'Upload your own photo';
  uploadBtn.style.cssText = [
    'position:absolute; bottom:8px; right:8px;',
    'background:rgba(0,0,0,.55); color:#fff; border-radius:6px;',
    'padding:5px 10px; font-size:0.75rem; cursor:pointer;',
    'backdrop-filter:blur(4px); transition:background .2s;',
  ].join('');
  uploadBtn.textContent = '📷 Upload photo';
  uploadBtn.onmouseover = () => uploadBtn.style.background = 'rgba(14,165,233,.85)';
  uploadBtn.onmouseout  = () => uploadBtn.style.background = 'rgba(0,0,0,.55)';

  const fileInput = document.createElement('input');
  fileInput.type   = 'file';
  fileInput.accept = 'image/*';
  fileInput.style.display = 'none';
  fileInput.addEventListener('change', () => handleUpload(prop.id, fileInput, img));

  uploadBtn.appendChild(fileInput);
  imgWrap.appendChild(uploadBtn);
  card.appendChild(imgWrap);

  // ── Content ────────────────────────────────────────────────
  const content = document.createElement('div');
  content.className = 'content';

  const title = document.createElement('div');
  title.className   = 'title';
  title.textContent = prop.title || 'Untitled Property';
  content.appendChild(title);

  const loc = document.createElement('div');
  loc.className   = 'location';
  loc.textContent = prop.address || prop.location || '';
  content.appendChild(loc);

  const price = document.createElement('div');
  price.className   = 'price';
  price.textContent = prop.price_numeric
    ? `PKR ${Number(prop.price_numeric).toLocaleString()}`
    : (prop.price ? `$${prop.price}` : '');
  content.appendChild(price);

  // Beds / Baths / Area specs
  const specParts = [];
  if (prop.beds)      specParts.push(`🛏 ${prop.beds} Beds`);
  if (prop.baths)     specParts.push(`🚿 ${prop.baths} Baths`);
  if (prop.area_sqft) specParts.push(`📐 ${Number(prop.area_sqft).toLocaleString()} sqft`);
  if (prop.specs)     specParts.push(prop.specs);

  if (specParts.length) {
    const specs = document.createElement('div');
    specs.className   = 'specs';
    specs.textContent = specParts.join('  ·  ');
    content.appendChild(specs);
  }

  if (prop.description) {
    const desc = document.createElement('div');
    desc.className   = 'description';
    desc.textContent = prop.description;
    content.appendChild(desc);
  }

  if (prop.amenities && Array.isArray(prop.amenities)) {
    const amenitiesDiv = document.createElement('div');
    amenitiesDiv.className = 'amenities';
    prop.amenities.forEach(a => {
      const span = document.createElement('span');
      span.textContent = a;
      amenitiesDiv.appendChild(span);
    });
    content.appendChild(amenitiesDiv);
  }

  const actions = document.createElement('div');
  actions.className = 'actions';
  const btnDetails = document.createElement('button');
  btnDetails.textContent = 'Details';
  btnDetails.onclick = () => alert('Details for ' + prop.title);
  const btnContact = document.createElement('button');
  btnContact.textContent = 'Contact';
  btnContact.onclick = () => alert('Contact agent for ' + prop.title);
  actions.appendChild(btnDetails);
  actions.appendChild(btnContact);
  content.appendChild(actions);

  card.appendChild(content);
  return card;
}

async function handleUpload(propertyId, fileInput, imgEl) {
  const file = fileInput.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('property_id', propertyId);
  formData.append('file', file);

  try {
    const res  = await fetch('/api/upload_image', { method: 'POST', body: formData });
    const data = await res.json();
    if (data.url) {
      imgEl.src = data.url + '?t=' + Date.now();   // cache-bust
    } else {
      alert('Upload failed: ' + (data.error || 'Unknown error'));
    }
  } catch (err) {
    console.error('Upload error:', err);
    alert('Upload failed. Check console.');
  }
}

