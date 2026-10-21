<section class="contact" id="epikoinonia">
  <div class="container contact-grid">
    <div>
      <h2>Ζητήστε προσφορά</h2>
      <p>Πείτε μας διάσταση και ποσότητα και θα σας απαντήσουμε άμεσα με τιμή και χρόνο παράδοσης.</p>
      <ul class="contact-list">
        <li><span>Τηλέφωνο</span><a href="tel:<?php echo esc_attr( KSILAKIA_PHONE ); ?>"><?php echo esc_html( KSILAKIA_PHONE_DISPLAY ); ?></a></li>
        <li><span>WhatsApp</span><a href="<?php echo esc_url( ksilakia_whatsapp_url() ); ?>" rel="noopener" target="_blank"><?php echo esc_html( KSILAKIA_WHATSAPP_DISPLAY ); ?></a></li>
        <li><span>Email</span><a href="mailto:<?php echo esc_attr( KSILAKIA_EMAIL ); ?>"><?php echo esc_html( KSILAKIA_EMAIL ); ?></a></li>
        <li><span>Διεύθυνση</span><a href="<?php echo esc_url( KSILAKIA_MAPS ); ?>" rel="noopener" target="_blank"><?php echo esc_html( KSILAKIA_ADDRESS ); ?></a></li>
      </ul>
    </div>
    <form class="form" id="ksilakia-contact" method="post">
      <input type="text" name="website" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
      <label>Όνομα / Επιχείρηση<input type="text" name="name" required autocomplete="name"></label>
      <label>Τηλέφωνο<input type="tel" name="phone" required autocomplete="tel"></label>
      <label>Email<input type="email" name="email" autocomplete="email"></label>
      <label>Διάσταση
        <select name="size">
          <option>215 × 3,2 mm</option>
          <option>215 × 4 mm</option>
          <option>240 × 4 mm</option>
          <option<?php selected( is_page( 'ksilakia-xoris-myti' ) ); ?>>Ξυλάκι χωρίς μύτη (παλέτα)</option>
          <option>Άλλη / δεν ξέρω</option>
        </select>
      </label>
      <label>Ποσότητα & σχόλια<textarea name="message" rows="4" placeholder="π.χ. 50.000 τεμ. τον μήνα, για μηχανή SM7000"></textarea></label>
      <button type="submit" class="btn">Αποστολή</button>
      <p class="form-msg" role="status"></p>
    </form>
  </div>
</section>
