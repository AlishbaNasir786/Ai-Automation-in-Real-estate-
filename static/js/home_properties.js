document.addEventListener('DOMContentLoaded', () => {
  loadProperties();
});

async function loadProperties() {
  try {
    const response = await fetch('/api/properties');
    if (!response.ok) throw new Error('Network response was not ok');
    const properties = await response.json();
    const container = document.getElementById('propertyShowcase');
    if (!container) return;
    container.innerHTML = '';
    properties.forEach(prop => {
      const card = document.createElement('div');
      card.className = 'property-card';

      const img = document.createElement('img');
      img.src = prop.image_url || 'https://via.placeholder.com/400x200?text=No+Image';
      img.alt = prop.title || 'Property Image';
      card.appendChild(img);

      const content = document.createElement('div');
      content.className = 'content';

      const title = document.createElement('div');
      title.className = 'title';
      title.textContent = prop.title || 'Untitled Property';
      content.appendChild(title);

      const loc = document.createElement('div');
      loc.className = 'location';
      loc.textContent = prop.location || '';
      content.appendChild(loc);

      const price = document.createElement('div');
      price.className = 'price';
      price.textContent = prop.price ? `$${prop.price}` : '';
      content.appendChild(price);

      if (prop.specs) {
        const specs = document.createElement('div');
        specs.className = 'specs';
        specs.textContent = prop.specs;
        content.appendChild(specs);
      }

      if (prop.description) {
        const desc = document.createElement('div');
        desc.className = 'description';
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
      container.appendChild(card);
    });
  } catch (err) {
    console.error('Failed to load properties:', err);
  }
}
