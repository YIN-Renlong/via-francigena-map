<?php
/**
 * Plugin Name: Via Francigena Map Updater
 * Description: 1-Click updater to pull the latest interactive map from GitHub. Now features Normal and Force Rebuild modes.
 * Version: 2.0 (Dual-Mode Architecture)
 * Author: YIN Renlong
 */

if ( ! defined( 'ABSPATH' ) ) exit; // Exit if accessed directly

global $vfm_copy_errors;
$vfm_copy_errors = array();

// 1. Add the Dropdown Menu to the Top Admin Bar
add_action( 'admin_bar_menu', 'vfm_add_admin_bar_button', 100 );
function vfm_add_admin_bar_button( $admin_bar ) {
    if ( ! current_user_can( 'manage_options' ) ) return; 

    // Main Menu Item
    $admin_bar->add_node( array(
        'id'    => 'vfm-map-menu',
        'title' => '🗺️ Map Sync',
        'meta'  => array( 'title' => 'Sync Map with GitHub' )
    ));

    // Sub-Item 1: Normal Update
    $admin_bar->add_node( array(
        'id'     => 'vfm-update-normal',
        'parent' => 'vfm-map-menu',
        'title'  => '🔵 Update Map (Normal)',
        'href'   => wp_nonce_url( admin_url( 'admin-post.php?action=vfm_do_update&mode=normal' ), 'vfm_update_nonce' ),
        'meta'   => array( 'title' => 'Overwrites files, but leaves old deleted files behind.' )
    ));

    // Sub-Item 2: Force Rebuild (The Nuke Option)
    $admin_bar->add_node( array(
        'id'     => 'vfm-update-force',
        'parent' => 'vfm-map-menu',
        'title'  => '🔴 Force Rebuild (Wipe & Sync)',
        'href'   => wp_nonce_url( admin_url( 'admin-post.php?action=vfm_do_update&mode=force' ), 'vfm_update_nonce' ),
        'meta'   => array( 'title' => 'DANGER: Deletes the entire /map folder first, then rebuilds from scratch.' )
    ));
}

// 2. Handle the Button Clicks
add_action( 'admin_post_vfm_do_update', 'vfm_handle_update' );
function vfm_handle_update() {
    global $wp_filesystem, $vfm_copy_errors;

    if ( ! current_user_can( 'manage_options' ) || ! isset( $_GET['_wpnonce'] ) || ! wp_verify_nonce( $_GET['_wpnonce'], 'vfm_update_nonce' ) ) {
        wp_die( 'Security check failed.' );
    }

    $mode = isset( $_GET['mode'] ) ? $_GET['mode'] : 'normal';

    require_once( ABSPATH . 'wp-admin/includes/file.php' );
    WP_Filesystem();

    $github_zip_url = 'https://github.com/YIN-Renlong/via-francigena-map/archive/refs/heads/main.zip?nocache=' . time();
    $target_dir = ABSPATH . 'map'; 
    $temp_dir = WP_CONTENT_DIR . '/vfm_temp_extract'; 

    // Step A: Download the ZIP
    $tmp_zip = download_url( $github_zip_url );
    if ( is_wp_error( $tmp_zip ) ) {
        wp_redirect( admin_url( '?vfm_status=error_download' ) );
        exit;
    }

    // Step B: Unzip to temp folder
    $unzip_result = unzip_file( $tmp_zip, $temp_dir );
    unlink( $tmp_zip ); 

    if ( is_wp_error( $unzip_result ) ) {
        wp_redirect( admin_url( '?vfm_status=error_unzip' ) );
        exit;
    }

    $source_dir = $temp_dir . '/via-francigena-map-main';

    // ==========================================
    // STEP C: THE FORCE WIPE LOGIC
    // ==========================================
    if ( $mode === 'force' ) {
        // If Force Mode, we completely annihilate the /map folder and everything inside it!
        if ( $wp_filesystem->exists( $target_dir ) ) {
            $wp_filesystem->delete( $target_dir, true ); // true = recursive delete
        }
    }

    // Ensure the target directory exists before copying
    if ( ! is_dir( $target_dir ) ) {
        wp_mkdir_p( $target_dir ); 
    }

    // Step D: Copy fresh files over
    $copy_success = vfm_recursive_copy_and_filter( $source_dir, $target_dir );

    // Step E: Cleanup temp folder
    $wp_filesystem->delete( $temp_dir, true );

    // Step F: Redirect to show success message
    if ( $copy_success ) {
        $status_code = ($mode === 'force') ? 'success_force' : 'success_normal';
        wp_redirect( admin_url( '?vfm_status=' . $status_code ) );
    } else {
        set_transient( 'vfm_copy_error_log', implode( '<br>', $vfm_copy_errors ), 60 );
        wp_redirect( admin_url( '?vfm_status=error_copy' ) );
    }
    exit;
}

// 3. Custom Copy Function
function vfm_recursive_copy_and_filter( $src, $dst ) {
    global $vfm_copy_errors;
    $dir = opendir( $src );
    @mkdir( $dst, 0755, true );
    $success = true;

    while ( false !== ( $file = readdir( $dir ) ) ) {
        if ( ( $file != '.' ) && ( $file != '..' ) ) {
            
            // Ignore backend scripts
            $blacklist = array( 'kml_raw', '.github', '.gitignore', 'README.md' );
            if ( in_array( $file, $blacklist ) ) continue;
            if ( pathinfo( $file, PATHINFO_EXTENSION ) === 'py' ) continue;

            $src_path = $src . '/' . $file;
            $dst_path = $dst . '/' . $file;

            if ( is_dir( $src_path ) ) {
                $res = vfm_recursive_copy_and_filter( $src_path, $dst_path );
                if ( !$res ) $success = false;
            } else {
                // Copy the file
                $res = copy( $src_path, $dst_path );
                if ( !$res ) {
                    $success = false;
                    $vfm_copy_errors[] = "Failed to copy: " . $dst_path; 
                }
            }
        }
    }
    closedir( $dir );
    return $success;
}

// 4. Show the Notification Messages
add_action( 'admin_notices', 'vfm_admin_notices' );
function vfm_admin_notices() {
    if ( ! isset( $_GET['vfm_status'] ) ) return;

    $status = $_GET['vfm_status'];
    
    if ( $status === 'success_normal' ) {
        echo '<div class="notice notice-success is-dismissible"><p>🔵 <strong>Normal Sync Complete!</strong> Files were overwritten successfully. <a href="/map/" target="_blank">View Map</a></p></div>';
    } elseif ( $status === 'success_force' ) {
        echo '<div class="notice notice-success is-dismissible" style="border-left-color: #c0392b;"><p>🔴 <strong>Force Rebuild Complete!</strong> The /map folder was completely wiped and rebuilt from scratch. No ghost files remain! <a href="/map/" target="_blank">View Map</a></p></div>';
    } elseif ( $status === 'error_download' ) {
        echo '<div class="notice notice-error is-dismissible"><p>❌ <strong>Error:</strong> Could not download the ZIP file from GitHub.</p></div>';
    } elseif ( $status === 'error_unzip' ) {
        echo '<div class="notice notice-error is-dismissible"><p>❌ <strong>Error:</strong> Could not unzip the file. Check server permissions.</p></div>';
    } elseif ( $status === 'error_copy' ) {
        $error_log = get_transient( 'vfm_copy_error_log' );
        echo '<div class="notice notice-error is-dismissible">';
        echo '<p>⚠️ <strong>Warning:</strong> Some files could not be copied due to server permissions.</p>';
        if ( $error_log ) { echo '<p><strong>Details:</strong><br>' . $error_log . '</p>'; }
        echo '</div>';
        delete_transient( 'vfm_copy_error_log' );
    }
}
?>