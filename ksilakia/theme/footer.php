</main>
<footer class="site-footer">
  <div class="container footer-grid">
    <div>
      <p class="logo"><span>ksilakia<b>.gr</b></span></p>
      <p><?php echo esc_html( KSILAKIA_COMPANY ); ?><br><?php echo esc_html( KSILAKIA_ADDRESS ); ?><br>Τηλ. <a href="tel:<?php echo esc_attr( KSILAKIA_PHONE ); ?>"><?php echo esc_html( KSILAKIA_PHONE_DISPLAY ); ?></a><br><a href="mailto:<?php echo esc_attr( KSILAKIA_EMAIL ); ?>"><?php echo esc_html( KSILAKIA_EMAIL ); ?></a></p>
    </div>
    <div>
      <h4>Τα sites μας</h4>
      <ul>
        <li><a href="https://crazysouvle.gr" rel="noopener">crazysouvle.gr</a> — Μηχανές σουβλακιών & εξοπλισμός</li>
        <li><a href="https://insouvlaki.com" rel="noopener">insouvlaki.com</a> — Μηχανές σουβλακιών</li>
        <li><a href="https://karvouno.gr" rel="noopener">karvouno.gr</a> — Φυσικό αυτοαναφλεγόμενο κάρβουνο</li>
        <li><a href="https://butcherequip.gr" rel="noopener">butcherequip.gr</a> — Εξοπλισμός κρεοπωλείου</li>
      </ul>
    </div>
    <div>
      <h4>Χρήσιμα</h4>
      <ul>
        <li><a href="<?php echo esc_url( wc_get_page_permalink( 'shop' ) ); ?>">Προϊόντα</a></li>
        <li><a href="<?php echo esc_url( ksilakia_page_url( 'xondriki-b2b' ) ); ?>">Χονδρική B2B</a></li>
        <li><a href="<?php echo esc_url( wc_get_page_permalink( 'myaccount' ) ); ?>">Ο λογαριασμός μου</a></li>
        <li><a href="<?php echo esc_url( ksilakia_page_url( 'epikoinonia' ) ); ?>">Επικοινωνία</a></li>
        <li><a href="<?php echo esc_url( ksilakia_page_url( 'oroi-xrisis' ) ); ?>">Όροι χρήσης & αποστολές</a></li>
        <li><a href="<?php echo esc_url( get_privacy_policy_url() ?: ksilakia_page_url( 'politiki-aporritou' ) ); ?>">Πολιτική απορρήτου</a></li>
      </ul>
    </div>
  </div>
  <div class="container copy">© <?php echo esc_html( date_i18n( 'Y' ) ); ?> ksilakia.gr — Καλαμάκια για σουβλάκια (ξυλάκια σουβλακιού) bamboo <a href="https://www.vnsrl.com/" target="_blank" rel="noopener">VN srl</a>. Με επιφύλαξη παντός δικαιώματος.</div>
</footer>
<a href="<?php echo esc_url( ksilakia_whatsapp_url() ); ?>" class="wa-float" rel="noopener" target="_blank" aria-label="WhatsApp">
  <svg viewBox="0 0 32 32" width="30" height="30" aria-hidden="true"><path fill="#fff" d="M16 3C9 3 3.3 8.7 3.3 15.7c0 2.5.7 4.9 2 7L3 29l6.5-2.1c2 1.1 4.2 1.7 6.5 1.7 7 0 12.7-5.7 12.7-12.7S23 3 16 3zm0 23.2c-2 0-4-.6-5.7-1.6l-.4-.2-3.9 1.2 1.3-3.7-.3-.4a10.4 10.4 0 0 1-1.6-5.6C5.4 9.9 10.2 5.2 16 5.2S26.6 9.9 26.6 15.7 21.8 26.2 16 26.2zm5.8-7.8c-.3-.2-1.9-.9-2.2-1-.3-.1-.5-.2-.7.2l-1 1.2c-.2.2-.4.2-.7.1-.3-.2-1.3-.5-2.5-1.6-.9-.8-1.6-1.9-1.8-2.2-.2-.3 0-.5.1-.6l.5-.6.3-.5c.1-.2 0-.4 0-.5l-1-2.4c-.3-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.4-.3.3-1.1 1.1-1.1 2.7s1.2 3.2 1.3 3.4c.2.2 2.3 3.5 5.5 4.9 2.7 1.1 3.3.9 3.9.8.6-.1 1.9-.8 2.2-1.5.3-.7.3-1.4.2-1.5-.1-.2-.3-.3-.6-.4z"/></svg>
</a>
<?php wp_footer(); ?>
</body>
</html>
